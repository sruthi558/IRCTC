import pymongo
import argparse
import shutil

cl = pymongo.MongoClient('mongodb://localhost:27017')
db = cl.irctc_backend_test_4


def confirm_prompt(question: str) -> bool:
    reply = None
    while reply not in ("y", "n"):
        reply = input(f"{question} (y/n): ").casefold()
    return (reply == "y")


def deleteMongo():
    db.asn_collection.drop()
    db.ip_collection.drop()
    # db.irctc_brand_mon_test_1.drop()
    db.irctc_dash_test_1.drop()
    db.irctc_file_test_1.drop()
    db.irctc_pnr_test_1.drop()
    db.irctc_susids_dash_test_1.drop()
    db.irctc_user_dash_test_1.drop()
    db.irctc_userid_data_test_1.drop()


def deleteSQLDB():
    shutil.rmtree('instance')
    shutil.rmtree('uploads')


def main(argument):
    if argument == 1:
        if not confirm_prompt("Are you sure you want to delete mongo?"):
            exit()
        deleteMongo()
        print('Mongo Deleted')
    elif argument == 2:
        if not confirm_prompt("Are you sure you want to delete SQLDB?"):
            exit()
        deleteSQLDB()
        print('SQLDB and uploads deleted')
    elif argument == 3:
        if not confirm_prompt("Are you sure you want to delete BOTH?"):
            exit()
        deleteMongo()
        deleteSQLDB()
        print('Both mongo and Sql deleted')
    else:
        print('Please select values between 1 2 3')
        exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--de", help="What to delete", required=True)
    args = parser.parse_args()
    try:
        main(int(args.de))
    except Exception as e:
        print(repr(e))
        print('Please enter values between 1,2,3')
