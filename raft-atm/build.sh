#!/bin/bash

sudo rm -f journal/* dump/* db/*
docker compose build
