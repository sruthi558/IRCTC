tmux new-session -d
tmux send-keys 'source env/bin/activate' C-m
tmux send-keys 'cd user_id_resp' C-m
tmux send-keys 'python3 app.py' C-m
tmux rename-session -t 4 'user'