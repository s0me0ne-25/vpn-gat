#!/bin/bash
cd $( dirname $0 )
cat "$1" | grep -vE '(^$|#)'
