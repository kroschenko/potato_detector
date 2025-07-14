#!/bin/bash
gettime() {
    date +%s
}
cd /home/user/potato_detector
source venv/bin/activate
start_time=$(gettime)
python main.py
end_time=$(gettime)
difference=$((end_time - start_time))
echo "program running time: $difference s"