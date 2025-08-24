module.exports = {
  apps: [
    {
      name: 'backend',
      script: 'python3',
      args: 'main.py',
      cwd: '/home/user/webapp/src',
      interpreter: 'none',
      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'frontend',
      script: 'npm',
      args: 'run dev',
      cwd: '/home/user/webapp/frontend'
    }
  ]
};