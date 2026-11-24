from agent import process_email

for test_id in ["x1", "x2", "x3", "x4"]:
    print(test_id, process_email({"id": test_id}))