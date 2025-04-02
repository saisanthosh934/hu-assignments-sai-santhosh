import os
import sys
import subprocess
import shutil
import tempfile
import pwd
import time  # testing to resolve error


# Verify existing user permissions and elevate to rot if needed
def elevate_to_root():
    if os.geteuid() != 0:
        print("You are not root. Elevating now...")
        try:
            print(
                f'sys executable {sys.executable} , sys aruments are {sys.argv}')  # testing to resolve error
            time.sleep(10)  # testing to resolve error
            print(
                f'System executable is {sys.executable} and SYS ARGV is {sys.argv}')
            subprocess.run(['sudo', sys.executable] + sys.argv, check=True)
            print(
                f'System executable is {sys.executable} and SYS ARGV is {sys.argv}')
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            print("Process failed while elevating to root", file=sys.stderr)
            sys.exit(1)


# Validate username for length and alphanumeric
def validate_username(username):
    if not username.isalnum() or len(username) > 10:
        print("Username is not valid. Make sure it alphanumeric and less than 10 charecters", file=sys.stderr)
        return False

    try:
        subprocess.run(['id', username], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"User {username} already exists.", file=sys.stderr)
        return False
    except subprocess.CalledProcessError:
        return True

# Email validation to send email containing private key


def validate_email(email):
    if '@' in email and '.' in email.split('@')[-1]:
        return True
    print("Please enter correct email", file=sys.stderr)
    return False


# Validate of path given by user is correct.
def validate_public_key(key_path):
    try:
        with open(key_path, 'r') as f:
            key = f.read().strip()
        if key.startswith('ssh-rsa ') or key.startswith('ssh-ed25519 ') or key.startswith('ssh-dss '):
            return True
        print("The path you entered do not contain valid SSH key", file=sys.stderr)
    except Exception as e:
        print(f"Error reading public key file: {e}", file=sys.stderr)
    return False


# Generating SSH keys for new user in temp file
def generate_ssh_key(username):
    key_dir = tempfile.mkdtemp(prefix=f"{username}_ssh_keys_")
    # testing to resolve error
    print(f'Temporary Key directory created at: {key_dir}')
    private_key_path = os.path.join(key_dir, "id_rsa")
    print(f'Private key path: {private_key_path}')  # testing to resolve error
    public_key_path = f"{private_key_path}.pub"
    print(f'Public key path: {public_key_path}')  # testing to resolve error

    try:
        subprocess.run([
            'ssh-keygen',
            '-t', 'rsa',
            '-b', '4096',
            '-f', private_key_path,
            '-N', '',
            '-q'
        ], check=True)

        os.chmod(private_key_path, 0o600)
        return public_key_path, private_key_path, key_dir
    except Exception as e:     # If we face any issue while geerating the keys , we will be removing temp direc tory too to ensure security
        print(f"Failed to generate SSH keys: {str(e)}", file=sys.stderr)
        if os.path.exists(key_dir):
            shutil.rmtree(key_dir)
        sys.exit(1)

# Creating user , directories and necessary access


def create_user(username, public_key_path, private_key_path):
    try:
        subprocess.run(['adduser', '--disabled-password',
                       '--gecos', '', username], check=True)
        subprocess.run(['usermod', '-aG', 'sudo', username], check=True)

        ssh_dir = f"/home/{username}/.ssh"
        os.makedirs(ssh_dir, mode=0o700, exist_ok=True)

        user_info = pwd.getpwnam(username)         # Obtaining usernmae
        # obtaining userid and groupid from username
        os.chown(ssh_dir, user_info.pw_uid, user_info.pw_gid)

        authorized_keys_path = f"{ssh_dir}/authorized_keys"

        # authorized_keys_path = f"{ssh_dir}/authorized_keys/"   # testing to resolve error
        public_key_dest = f"{authorized_keys_path}"
        shutil.copy(public_key_path, public_key_dest)

        # This is a temporary setup as we dont have a way to send private key to client. We are storing on server userhome directory - Not a production grade
        shutil.copy(private_key_path, f"{ssh_dir}/{username}_private_key.pem")
        os.chown(f"{ssh_dir}/{username}_private_key.pem",
                 user_info.pw_uid, user_info.pw_gid)
        # This is a temporary setup as we dont have a way to send private key to client. We are storing on server userhome directory - Not a production grade

        os.chmod(public_key_dest, 0o600)
        os.chown(public_key_dest, user_info.pw_uid, user_info.pw_gid)

        print(f"\n{username} user created successfully with sudo privileges.")
    except Exception as e:
        print(
            f"Failed to create user: {str(e)}", file=sys.stderr)
        subprocess.run(['userdel', '--remove', username],
                       stderr=subprocess.DEVNULL)  # If sor some reason process failes we wanna delete user
        sys.exit(1)


def main():

    elevate_to_root()

    print("STarting Script Here...")

    while True:
        username = input("Enter new username: ").strip()
        if validate_username(username):
            break

    while True:
        email = input("Enter user's email address for key delivery: ").strip()
        if validate_email(email):
            break

    use_existing = input(
        "Do you have an existing keypath of public key ?? (y/n): ").strip().lower()

    if use_existing == 'y':
        while True:  # Prompt for existing public key path until valid key is given as user is having it
            public_key_path = input(
                "Enter path to existing public key: ").strip()
            if validate_public_key(public_key_path):
                break
        private_key_path = None
        key_dir = None
    else:
        print("\nGenerating SSH key pair...")
        public_key_path, private_key_path, key_dir = generate_ssh_key(username)

    print("\nCreating user and setting up SSH access.....")
    create_user(username, public_key_path, private_key_path)

    # Display private key if it was generated
    # Need to discuss with Shane as we dont have any cleint to send email hwo do we handle it
    # if private_key_path:
    #     with open(private_key_path, 'r') as f:
    #         private_key = f.read()
    #     print("=" * 50)
    #     print("PRIVATE KEY - SAVE THIS SECURELY")
    #     print("=" * 50)
    #     print(private_key)
    #     print("=" * 50)
    #     print("IMPORTANT: This private key will not be shown again.")
    #     print("=" * 50)

    # Clean up temporary files if they exist
    if key_dir and os.path.exists(key_dir):
        shutil.rmtree(key_dir)
    print("\nEnding script here...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}", file=sys.stderr)
        sys.exit(1)
