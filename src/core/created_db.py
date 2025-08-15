# 테이블 생성 스크립트
from database import create_tables, drop_tables
import sys

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "create":
            create_tables()
        elif command == "drop":
            confirm = input("모든 테이블을 삭제하시겠습니까? (yes/no): ")
            if confirm.lower() == "yes":
                drop_tables()
            else:
                print("취소되었습니다")

        elif command == "reset":
            confirm = input("모든 테이블을 삭제하고 다시 생성하시겠습니까? (yes/no):")
            if confirm.lower() == "yes":
                drop_tables()
                create_tables()
            else:
                print("취소되었습니다.")
        else:
            print("사용법: python create_db.py[create|drop|reset]")
    else:
        print("사용법: python create_db.py[create|drop|reset]")

if __name__ == "__main__":
    main()