#!/bin/bash

# Smart Speaker Conversation Analysis Platform - Launch Script
# 智能音箱對話分析平台 - 啟動腳本

echo "Starting Smart Speaker Conversation Analysis Platform..."
echo "智能音箱對話分析平台啟動中..."

# Use the conda Python interpreter
/Users/timshieh/Documents/aiello/apps/hotel_review_tool/.conda/bin/python -m streamlit run app.py --server.port 8502
