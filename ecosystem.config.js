module.exports = {
  apps: [{
    name: 'google-keyword-planner-mcp',
    script: '.venv/bin/python',
    args: 'src/main.py',
    cwd: '/Users/mac/kodziki/mcp/google-keyword-planner-mcp',
    interpreter: 'none',
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      PYTHONUNBUFFERED: '1'
    },
    error_file: 'logs/error.log',
    out_file: 'logs/out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss'
  }]
};
