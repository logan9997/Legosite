SCHEMA="public"
DB="legosite_DB"
USER="postgres"
PASSWORD="#Legomario1"
PORT="5432"
HOST="127.0.0.1"

# declare -a StringArray=()
# for val in ${StringArray[@]}; do
#  echo $val
# done

# var=$(psql -Atc "select lower(tablename) from pg_tables where schemaname='public'" legosite_DB)
read vars <<< $(psql -Atc "select lower(tablename) from pg_tables where schemaname='public'" legosite_DB)
for i in "${vars[@]}"; do
    echo $i
done