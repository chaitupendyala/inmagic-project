from pymarc import MARCReader, Field, Subfield
from tkinter.filedialog import askopenfilename
import re
from copy import deepcopy

# Function to split a comma-separated string of issues into a list
def breakIntoIssues(issues):
    ret = []
    for issue in issues.split(","):
        ret.append(issue.strip())
    return ret

# Function to clean and convert issue month names to their corresponding numbers
def cleanIssueMonth(issue_month):
    issue_month = issue_month.lower().strip()
    issue_months = {'spring':'21', 'spr':'21', 'summer':'22', 'sum':'22', 'autum':'23', 'aut':'23', 'winter':'24', 'win':'24'}
    for month, month_number in issue_months.items():
        if re.search(month, issue_month):
            issue_month = issue_month.replace(month, month_number)
    return issue_month

# Function to extract issue number and month from an issue string
def extractIssueNumberAndMonth(issue):
    if len(issue) == 0:
        return []

    issueNumber, issueMonth = "", ""
    if issue[0] in "0123456789":
        issueSplit = issue.split(" ", 1)
        if len(issueSplit) > 1:
            issueNumber, issueMonth = issueSplit
        else:
            issueNumber = issueSplit[0]
    elif issue[0] == "[":
        issueMonth = issue
    else:
        return []

    if issueMonth:
        issueMonth = issueMonth.replace("[", "")
        issueMonth = issueMonth.replace("]", "")
        issueMonth = cleanIssueMonth(issueMonth)

    return [issueNumber, issueMonth]

# Function to read MARC records from a file
def readFile(filename):
    file = None
    records = []
    try:
        print(f"Entering readFile(filename) with the following filename {filename}")
        with open(filename, 'rb') as f:
            file = MARCReader(f)
            if file:
                records = parseFile(file)
    except Exception as e:
        raise e
    finally:
        print(f"Exiting readFile(filename) method with the following file {file}")
    return records

# Function to create a new MARC file from a list of records
def create_new_file(records, file_name):
    my_new_marc_filename = "my_new_marc_file.txt" if file_name is None else file_name
    with open(my_new_marc_filename, 'w', encoding='utf-8') as data:
        for record in records:
            data.write(str(record) + "\n\n")

# Function to parse MARC records and extract issue information
def parseFile(marcReaderObject):
    records = []
    try:
        print(f"Entering parseFile(marcReaderObject) method with marcReaderObject {marcReaderObject}")
        new_007_field = Field(
            tag='007',
            data='ta'
        )
        for record in marcReaderObject:
            if record is None:
                continue
            new_record = deepcopy(record)
            if '866' in new_record:
                text = new_record['866']['a']
                year_pattern = r'(\d{4}):\s?(\d+)?\s*\((.*?)\)'
                matches = re.findall(year_pattern, text)
                formatted_text = []
                contain_volume = False
                contain_issue_number = False
                contain_issue_month = False
                i = 1
                for year, volume, content in matches:
                    issues = breakIntoIssues(content)
                    issues_text = []
                    contain_range = False
                    if volume != "":
                        contain_volume = True
                    for issue in issues:
                        ret = extractIssueNumberAndMonth(issue)
                        if not ret:
                            continue
                        issue_number, issue_month = ret
                        if issue_number != "":
                            contain_issue_number = True
                        if issue_month != "":
                            contain_issue_month = True
                        issues_text.append([year, volume, issue_number, issue_month])
                    for year, volume, issue_number, issue_month in issues_text:
                        if not year and not volume and not issue_number and not issue_month:
                            continue
                        new_863_field = Field(
                            tag='863',
                            indicators=['40' if '-' in issue_month or '-' in issue_number else '41', '$8 ', f'1.{i} '],
                            subfields=[
                                Subfield(code='a', value=f' {year} ')
                            ]
                        )
                        cur = 'b'
                        if contain_volume:
                            new_863_field.subfields.append(Subfield(code=cur, value=f' {volume} '))
                            cur = chr(ord(cur) + 1)
                        if contain_issue_number:
                            new_863_field.subfields.append(Subfield(code=cur, value=f' {issue_number} '))
                            cur = chr(ord(cur) + 1)
                        if contain_issue_month:
                            new_863_field.subfields.append(Subfield(code=cur, value=f' {issue_month} '))
                            cur = chr(ord(cur) + 1)
                        new_record.add_ordered_field(new_863_field)
                        formatted_text.append(f"=863 {40 if '-' in issue_number else 41}$8 1.{i} $a {year} $b {volume} $c {issue_number} $d {issue_month}")
                        i += 1
                new_853_field = Field(
                    tag='853',
                    indicators=['20', '$8 '],
                    subfields=[
                        Subfield(code='a', value=' (year) ')
                    ]
                )
                cur = 'b'
                if contain_volume:
                    new_853_field.subfields.append(Subfield(code=cur, value=' v. '))
                    cur = chr(ord(cur) + 1)
                if contain_issue_number:
                    new_853_field.subfields.append(Subfield(code=cur, value=' no. '))
                    cur = chr(ord(cur) + 1)
                if contain_issue_month:
                    new_853_field.subfields.append(Subfield(code=cur, value=' (month) '))
                    cur = chr(ord(cur) + 1)
                new_record.add_ordered_field(new_853_field)
                new_record.add_ordered_field(new_007_field)
                records.append(new_record)
    except Exception as e:
        raise e
    finally:
        print("Exiting parseFile(marcReaderObject) method")
    return records

if __name__ == "__main__":
    try:
        print("In the main function")
        fileName = askopenfilename()
        print(f"Following file chosen: {fileName}")
        records = readFile(fileName)
        create_new_file(records, fileName.replace('.mrc', '.txt'))
    except Exception as e:
        raise e
    finally:
        print("Exiting the main method.")