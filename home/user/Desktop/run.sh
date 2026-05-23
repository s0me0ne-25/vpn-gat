#!/bin/bash

# VPN-GAT main worker itself
# Set interval here below

while [[ true ]]; do
        /opt/vpn-gat/vpn-gat.py
        sleep 5m
done
