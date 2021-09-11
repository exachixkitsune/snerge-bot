#!/bin/sh

# SPDX-FileCopyrightText: 2020 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

PATHS="bot.py load.py snergism.py prosegen"

reuse lint
black $PATHS
flake8 $PATHS
mypy --strict $PATHS
pylint $PATHS
