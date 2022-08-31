from os.path import isfile, join
import csv
from datetime import datetime


class PpfSbiHelper:
    def __init__(self, file_locn):
        self.item = file_locn

    def get_transactions(self):
        if isfile(self.item) and self.item.endswith(".xls"):
            print("working with ", self.item)
            read_file = open(self.item, "r")
            temp_file = self.item.replace('.xls', '.csv')
            write_file = open(temp_file, "w")
            found_header = False
            acc_num = None
            for line in read_file:
                # print(line)
                if not found_header:
                    if line.startswith('Txn Date'):
                        found_header = True
                        write_file.write(line)
                    if line.startswith("Account Number"):
                        acc_num = line[line.find(":")+1:].strip().replace('_', '')
                        print(acc_num)
                else:
                    if not line.strip():
                        continue
                    if not "There is no financial transaction" in line and not "This is a computer generated" in line:
                        write_file.write(line)

            read_file.close()
            write_file.close()
            with open(temp_file, mode='r', encoding='utf-8-sig') as csv_file:
                print("opened file as csv:", temp_file)
                csv_reader = csv.DictReader(csv_file, dialect="excel-tab")
                line_count = 0
                for row in csv_reader:
                    if line_count == 0:
                        print(f'Column names are {", ".join(row)}')
                    print(row)
                    val = {"ppf_number": acc_num}
                    for k, v in row.items():
                        # Txn Date, Value Date, Description, Ref No./Cheque No.,         Debit, Credit, Balance
                        if 'Value Date' in k:
                            val["trans_date"] = datetime.strptime(
                                v, '%d %b %Y').date().strftime('%Y-%m-%d')
                        elif 'Description' in k:
                            val["notes"] = v
                            val["interest_component"] = "interest" in v.lower()
                        elif 'Ref No' in k:
                            val["reference"] = v
                        elif 'Debit' in k:
                            if v.strip():
                                val["type"] = "DR"
                                val["amount"] = int(v.strip().replace(',', ''))
                        elif 'Credit' in k:
                            if v.strip():
                                val["type"] = "CR"
                                val["amount"] = float(v.strip().replace(',', ''))
                    # print(val)
                    yield val
                    line_count += 1

