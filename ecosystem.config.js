module.exports = {
  apps: [{
    name: 'cdmbot',
    script: 'src/main.py',
    interpreter: 'python3',
    env: {
      NODE_ENV: 'production'
    }
  }]
}