#!/bin/bash

echo "running core db migrations"
yoyo apply --batch --database sqlite:///data/cache.db libs/sqlite/core/migrations
