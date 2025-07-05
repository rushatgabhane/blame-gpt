#!/bin/bash

echo "running core db migrations"
yoyo apply --batch --database sqlite:///data/cache.db libs/sqlite/core/migrations

echo "running docs db migrations"
yoyo apply --batch --database sqlite:///data/docs.db libs/sqlite/docs/migrations
