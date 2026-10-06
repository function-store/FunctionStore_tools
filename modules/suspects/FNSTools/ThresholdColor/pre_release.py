# Embody/PI pre_release hook -- runs on the STAGED COPY in /sys/quiet before
# the portable tox is written (extensions NOT initialized there; direct
# par/table edits only). args[0] = resolved save path.
#
# The generic strip is the whole job for now. Package-specific work goes
# BELOW this line, never above it (packaging/CREATING.md).
exec(open('packaging/pre_release_common.py').read())
