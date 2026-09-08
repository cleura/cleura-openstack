# `cleura-openstackclient`

Conveniently installs OpenStack clients for Cleura Cloud.

## Purpose

By `pip`-installing this meta-package into a virtual environment (venv), you populate your environment with [OpenStack](https://openstack.org) clients whose versions are expected to work with [Cleura Cloud](https://docs.cleura.cloud).

This package provides no functionality of its own; it only installs dependencies.

## Installation

To install from [PyPI](https://pypi.org/project/cleura-openstackclient/), run:

```shell
# using pip
pip install cleura-openstackclient==0.0.12
```
```shell
# using pipx
pipx install --include-deps cleura-openstackclient==0.0.12
```

To install directly from [the repository](https://github.com/cleura/cleura-openstackclient), run:

```shell
# using pip
pip install git+https://github.com/cleura/cleura-openstackclient@v0.0.12
```
```shell
# using pipx
pipx install --include-deps git+https://github.com/cleura/cleura-openstackclient@v0.0.12
```

Then, invoke the `openstack` command provided by the `python-openstackclient` package.

## License

Just like all other OpenStack client packages, `cleura-openstackclient` uses the Apache 2 license.
See [`LICENSE.txt`](LICENSE.txt) for details.
