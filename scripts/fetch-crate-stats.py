#!/usr/bin/env python3

import os
import subprocess
import tempfile
import re


BLOG_REPO = "https://github.com/rust-embedded/blog"
AWESOME_REPO = "https://github.com/rust-embedded/awesome-embedded-rust"


def extract_table(newsletter_path):
    f = open(newsletter_path, 'rt')
    data = f.read()
    f.close()

    state = 'idle'
    lines = []
    for line in data.split("\n"):
        if state == 'idle':
            if "## `embedded-hal` Ecosystem Crates" in line:
                state = 'wait-for-table'
        if state == 'wait-for-table':
            if line.startswith("|"):
                state = 'table'
        if state == 'table':
            if line.startswith('|'):
                lines.append(line)
            else:
                break
    if len(lines) == 0:
        return

    # Check sanity
    if len(lines) != 8:
        return

    slines = []
    for line in lines:
        a = line.split("|")
        a = a[1:-1]
        a = list(map(str.strip, a))
        slines.append(a)

    # Check header
    if slines[0] != ['Type', 'Status', 'Count', 'Diff']:
        return

    values = {}
    for line in slines[2:]:
        name = line[0]
        value = line[2]
        values[name] = value
    #print(values)
    return values, slines


def is_tamplate(values):
    if values is None:
        return False
    for v in values.values():
        if "?" in v:
            return True
    return False


def is_valid(values):
    if values is None:
        return False
    for v in values.values():
        if not v.isdecimal():
            return False
    return True


def calculate_current_values():
    path = os.path.join("awesome-embedded-rust", "README.md")
    f = open(path, "rt")
    data = f.read()
    f.close()

    # Extract level-2 headers
    content = {}
    current_header = None
    accumulated = []
    for line in data.split("\n"):
        if line.startswith("## "):
            if current_header is not None:
                content[current_header] = accumulated
            current_header = line[3:]
            accumulated = []
            continue
        accumulated.append(line)
    content[current_header] = accumulated

    header_map = {
        'Peripheral Access Crates':     '[Peripheral Access Crates]',
        'HAL implementation crates':    '[HAL Impl Crates]',
        'Board support crates':         '[Board Support Crates]',
        'Driver crates':               ('[Driver Crates Released]', '[Driver Crates WIP]'),
        'no-std crates':                '[no-std crates]',
    }
    values = {}
    for header in header_map.keys():
        if header not in content:
            raise Exception("Header %s not found" % header)
        count = 0
        count_wip = 0
        wip_seen = False
        for line in content[header]:
            if line.startswith('### WIP'):
                wip_seen = True
            if re.match(r'[\-*]\s+\[', line) or re.match(r'\d+\. ', line):
                count += 1
                if wip_seen:
                    count_wip += 1
        if header == 'Driver crates':
            captions = header_map[header]
            values[captions[0]] = count - count_wip
            values[captions[1]] = count_wip
        else:
            values[header_map[header]] = count - count_wip
    return values


def main():
    subprocess.check_call(["git", "clone", BLOG_REPO])
    subprocess.check_call(["git", "clone", AWESOME_REPO])

    newsletters = []
    blog_dir = os.path.join("blog", "content")
    for filename in os.listdir(blog_dir):
        if re.match(r'^\d+-\d+-\d+-newsletter-\d+\.md$', filename):
            newsletters.append(os.path.join(blog_dir, filename))
    newsletters.sort()

    print("Checking ", newsletters[-1])
    values, table = extract_table(newsletters[-1])
    if is_tamplate(values):
        print("Template table found, checking the previous newsletter")
        print("Checking ", newsletters[-2])
        values, table = extract_table(newsletters[-2])
    if not is_valid(values):
        raise Exception("Can't find valid table")
    for k in values.keys():
        values[k] = int(values[k])

    current_values = calculate_current_values()
    print("OLD:", values)
    print("NEW:", current_values)

    if sorted(values.keys()) != sorted(current_values.keys()):
        raise Exception("Table headers mismatch, check script!")

    diff = {}
    for header in values.keys():
        old_value = values[header]
        new_value = current_values[header]
        d = new_value - old_value
        if d == 0:
            d = '~'
        elif d > 0:
            d = '+' + str(d)
        else:
            d = str(d)
        diff[header] = d

    # Create (patch) table
    for i in range(2, len(table)):
        line = table[i]
        header = line[0]
        if header not in current_values:
            raise Exception("Invalid header: " + header)
        line[2] = str(current_values[header])
        line[3] = diff[header]

    # Calculate column sizes
    column_sizes = []
    for i in range(len(table[0])):
        max_column_size = 0
        for line in table:
            max_column_size = max(max_column_size, len(line[i]))
        column_sizes.append(max_column_size)

    # Format the table
    lines = []
    for table_line in table:
        s = "|"
        for (i, column_size) in enumerate(column_sizes):
            item = table_line[i]
            item = item + (' ' * (column_size - len(item)))
            s += " " + item + " |"
        lines.append(s)
    table = "\n".join(lines)

    print("Here is your table:\n\n")
    print(table)
    print("\n")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmpdirname:
        print('Created temporary directory:', tmpdirname)
        os.chdir(tmpdirname)

        main()
