import re
import glob
import os

r = re.compile(r'.*configured_value\([\'\"]([\w\.\-]+)[\'\"](,(.+))?\)')
r_error = re.compile(r'.*configured_value\(\s*$')

keys = []

for file in glob.iglob(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "newm", "**", "*.py"), recursive=True):
    if '__pycache__' in file:
        continue
    for line in open(file, 'r'):
        m = r.match(line)
        if m is not None:
            key, default = (m.group(1), m.group(3))
            default = default.strip() if default is not None else None
            check = [(k, d) for k, d in keys if k == key]
            if len(check) > 0:
                if check[0][1] != default:
                    print("ERROR: Detected inconsistent defaults: %s, %s != %s" % (key, default, check[0][1]))
            else:
                keys += [(key, default)]

        if r_error.match(line) is not None:
            print("ERROR: %s" % line)

print("|%-40s|%-40s|%-20s|" % ("Configuration key", "Default value", "Description"))
print("|%-40s|%-40s|%-20s|" % ("-"*40, "-"*40, "-"*20))
for k, d in sorted(keys, key=lambda k: k[0]):
    print("|%-40s|%-40s|                    |" % ("`%s`" % k, "" if d is None or d.strip() == "None" else "`%s`" % d))

for k, d in keys:
    r_check = re.compile(r'\|\s*(%s)\s*\|\s*(%s).*' % (re.escape("`%s`" % k), re.escape("" if d is None or d.strip() == "None" else "`%s`" % d)))
    r_check_weak = re.compile(r'\|\s*(%s).*' % (re.escape("`%s`" % k)))
    weak_m = None
    for l in open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "README.md"), 'r'):
        if r_check.match(l) is not None:
            break
        if r_check_weak.match(l) is not None:
            weak_m=l
    else:
        if weak_m is None:
            print("ERROR: README does not contain info for %s" % k)
        else:
            print("WARNING: Did not find default (%s) for %s in README" % (d, k))
