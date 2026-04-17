#!/usr/bin/env python3
"""
静态检查：解析 backend/models 中定义的 ORM 映射类，收集其属性名；
然后在工程中查找对这些类的实例化调用（例如 User(... )），报告传入的关键字参数中有哪些不在类属性集合内。

不会自动修改任何代码；仅用于发现潜在的 "invalid keyword" 错误。
"""
import ast
import os
import sys
from typing import Dict, Set, List, Tuple

ROOT = os.getcwd()
MODELS_DIR = os.path.join(ROOT, 'backend', 'models')

exclude_dirs = {'.git', 'node_modules', 'backend/venv', 'venv', 'frontend/dist'}


def should_skip_path(path: str) -> bool:
    for p in exclude_dirs:
        if p in path.replace('\\', '/'):
            return True
    return False


def gather_model_attributes(models_dir: str) -> Dict[str, Set[str]]:
    models = {}
    if not os.path.isdir(models_dir):
        print(f"Models directory not found: {models_dir}")
        return models
    for fname in os.listdir(models_dir):
        if not fname.endswith('.py'):
            continue
        p = os.path.join(models_dir, fname)
        try:
            src = open(p, 'r', encoding='utf-8').read()
            tree = ast.parse(src)
        except Exception as e:
            print(f"Failed to parse {p}: {e}")
            continue
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                # detect subclass of Base
                bases = []
                for b in node.bases:
                    if isinstance(b, ast.Name):
                        bases.append(b.id)
                    elif isinstance(b, ast.Attribute):
                        # e.g. config.db.Base
                        bases.append(b.attr)
                if 'Base' not in bases:
                    continue
                attrs = set()
                for stmt in node.body:
                    # AnnAssign covers 'name: type = mapped_column(...)'
                    if isinstance(stmt, ast.AnnAssign):
                        target = stmt.target
                        if isinstance(target, ast.Name):
                            attrs.add(target.id)
                    elif isinstance(stmt, ast.Assign):
                        for t in stmt.targets:
                            if isinstance(t, ast.Name):
                                attrs.add(t.id)
                models[node.name] = attrs
    return models


def find_model_instantiations(root: str, model_attrs: Dict[str, Set[str]]) -> List[Tuple[str,int,str,str]]:
    findings = []  # (file, lineno, class_name, invalid_kw)
    for dirpath, dirnames, filenames in os.walk(root):
        # filter out unwanted dirs
        if should_skip_path(dirpath):
            continue
        for fname in filenames:
            if not fname.endswith('.py'):
                continue
            fpath = os.path.join(dirpath, fname)
            if should_skip_path(fpath):
                continue
            try:
                src = open(fpath, 'r', encoding='utf-8').read()
                tree = ast.parse(src)
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    func_name = None
                    if isinstance(func, ast.Name):
                        func_name = func.id
                    elif isinstance(func, ast.Attribute):
                        # take last attribute name: e.g. models.user.User -> User
                        func_name = func.attr
                    if not func_name:
                        continue
                    if func_name in model_attrs:
                        allowed = model_attrs[func_name]
                        for kw in node.keywords:
                            if kw.arg is None:
                                # **kwargs or similar
                                continue
                            if kw.arg not in allowed:
                                findings.append((fpath, node.lineno, func_name, kw.arg))
    return findings


if __name__ == '__main__':
    models = gather_model_attributes(MODELS_DIR)
    if not models:
        print('No model classes detected under backend/models')
        sys.exit(0)
    print('Detected model classes and attributes:')
    for k,v in models.items():
        print(f' - {k}: {sorted(list(v))}')
    print('\nScanning project for instantiations...')
    findings = find_model_instantiations(ROOT, models)
    if not findings:
        print('\nNo mismatching keyword arguments found for model constructors.')
        sys.exit(0)
    print('\nPotential issues found:')
    for fpath, lineno, cls, kw in findings:
        print(f' - {fpath}:{lineno} -> {cls} called with unknown kw "{kw}"')
    sys.exit(1)
