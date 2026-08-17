#!/bin/bash
# 轻量内存监控：每 5 分钟运行，低内存时记录告警
MEM_AVAIL=$(awk '/MemAvailable/ {printf "%d", $2/1024}' /proc/meminfo)
if [ "$MEM_AVAIL" -lt 150 ]; then
  echo "$(date +%F\ %T) 警告: MemAvailable=${MEM_AVAIL}MB" >> /var/log/kebiao/mem-watch.log
elif [ "$MEM_AVAIL" -lt 100 ]; then
  echo "$(date +%F\ %T) 严重: MemAvailable=${MEM_AVAIL}MB，内存将耗尽" >> /var/log/kebiao/mem-watch.log
fi
