from .tools import run_cmd

def detect_runner(tech_stack: str):
    s = (tech_stack or "").lower()
    if "laravel" in s or "php" in s:
        return ("phpunit", "vendor/bin/phpunit || php artisan test --testdox")
    if "react" in s or "vite" in s or "jest" in s or "js" in s or "ts" in s:
        return ("jest", "npm test -- --watchAll=false || npx jest --ci --reporters=default")
    if "python" in s:
        return ("pytest", "pytest --maxfail=1 -q")
    return ("generic", "echo 'no tests configured'")

def run_tests(cwd: str, tech_stack: str):
    name, cmd = detect_runner(tech_stack)
    return run_cmd(cmd, cwd=cwd)
