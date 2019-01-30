echo "Updating ./locale/zh_CN/LC_MESSAGES/*.po"
make gettext && sphinx-intl update -p _build/gettext -l zh_CN