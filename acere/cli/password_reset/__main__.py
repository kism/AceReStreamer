from sqlmodel import Session, select

from acere.constants import DEFAULT_INSTANCE_PATH
from acere.crud import get_user_by_username, update_user
from acere.database.init import engine
from acere.database.models.user import User, UserUpdate
from acere.instances.paths import get_app_path_handler, setup_app_path_handler
from acere.utils.cli import console, prompt
from acere.version import PROGRAM_NAME, __version__


def main() -> None:
    """CLI for password reset."""
    console.print(f"{PROGRAM_NAME} Password Reset Tool v{__version__}")
    setup_app_path_handler(DEFAULT_INSTANCE_PATH)
    path_handler = get_app_path_handler()

    if path_handler.database_file.exists():
        console.print(f"Using database file at: {path_handler.database_file}\n")
    else:
        console.print(f"Database file not found at: {path_handler.database_file}\n")
        return

    # Note: db_path argument is currently not used, using the default engine
    with Session(engine) as session:
        # Print all users in the database
        users = session.exec(select(User)).all()
        if not users:
            console.print("No users found in the database.")
            return

        console.print("Existing users: \n" + "\n".join([f" {user.username}" for user in users]) + "\n")

        username = prompt("Enter the username to reset the password for:")
        user = get_user_by_username(session=session, username=username)
        if not user:
            console.print(f"User '{username}' not found.")
            return

        new_password = prompt(f"Enter the new password for user '{username}':")
        if not new_password:
            console.print("Password cannot be empty.")
            return

        user_update = UserUpdate(password=new_password)
        update_user(session=session, db_user=user, user_in=user_update)
        session.commit()
        console.print(f"Password for user '{username}' has been reset successfully.")


if __name__ == "__main__":
    main()
