module.exports = {
  apps: [{
    name: 'mooring-backend',
    script: 'python',
    args: '-m uvicorn src.main_simple:app --host 0.0.0.0 --port 8001 --reload',
    cwd: '/home/user/webapp',
    interpreter: 'none',
    env: {
      PYTHONPATH: '/home/user/webapp'
    }
  }]
};
