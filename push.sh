git add .
while true; do
  CMSG=$(./cmsg.py || echo "up")
  echo "Commit message: $CMSG"
  read -p "Do you like this one? (y/n) " yn
  case $yn in
  [Yy]*) break ;;
  [Nn]*) continue ;;
  *) continue ;;
  esac
done
git commit -m "$CMSG"
git push