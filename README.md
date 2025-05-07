# 🔫 pystolint 🔫

## Yet another python linter?

No. It's just a runner for [ruff](https://docs.astral.sh/ruff/) + [mypy](https://mypy.readthedocs.io/en/stable/) with [these](https://github.com/hhru/pystolint/blob/master/pystolint/default_config/pyproject.toml) settings


## Why?

I'm fed up with:
1. Having to copy settings for every single project. (at least until "parent pyproject.toml" is not invented)
2. Not being able to apply checks only to git diffs, which makes it hard to add linters to large projects
3. Not being able to deprecate certain things and preventing them in new code. 
    - [Solved for 3.13+](https://mypy.readthedocs.io/en/stable/changelog.html#support-for-deprecated-decorator-pep-702)


## Install

### Simple:
- `pip install pystolint`

or

- `pip install git+ssh://git@github.com/hhru/pystolint.git@master`

### Dev:

1. Clone repo
```
git clone git@github.com:hhru/pystolint.git ~/projects/pystolint
cd ~/projects/pystolint
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. Create global shortcut (/usr/local/bin/pys):
```
  #!/path/to/your/pystolint/.venv/bin/python
  import sys
  from pystolint.main import main

  if __name__ == '__main__':
    sys.exit(main())
```
3. Make executable:
```
chmod +x /usr/local/bin/pys
```


## Usage

Check code:
```bash
pys check .
pys check path1 path2
pys check --diff
```

Format code:

```bash
pys format .
pys format path1 path2
```


## Settings

can be specified from cli or pyproject.toml. cli settings have bigger priority

example toml:
```toml
[tool.pystolint]
base_toml_path = "/path/to/shared/config.toml"
base_branch_name = "develop"
```

cli:
- `--base_toml_path` - path or link for replace pystolint [default settings](https://github.com/hhru/pystolint/blob/master/pystolint/default_config/pyproject.toml)
- `--base_branch_name` - branch name from which to get diff (default is master)
- `--config` - specify path to toml configs (default is `pyproject.toml` in current dir)
