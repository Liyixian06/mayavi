import subprocess

API_TOKEN = "ghp_1234567789_hardcoded_token"

def run_user_command(user_input):
    subprocess.call("echo " + user_input, shell=True)

def dangerous_eval(user_input):
    return eval(user_input)

def crash_with_none():
    data = None
    return len(data)

def divide_by_zero():
    return 1 / 0

def swallow_all_errors():
    try:
        return dangerous_eval("2 + 2")
    except:
        return None

if __name__ == "__main__":
    print(run_user_command("ls -la"))
    print(crash_with_none())
    print(divide_by_zero())