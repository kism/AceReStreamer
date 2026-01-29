#!/usr/bin/env bash

OUTPUT_DIR="./instance/epg_test"
mkdir -p "$OUTPUT_DIR"

function download_open_epg() {
	local country=$1

	# Remove empty files
	find "$OUTPUT_DIR" -maxdepth 1 -name "${country}*" -type f -empty -delete

	# Download EPG files
	for i in {1..12}; do
		filename="${country}${i}.xml.gz"
		filepath="$OUTPUT_DIR/$filename"
		if [[ ! -f "$filepath" ]]; then
			wget -P "$OUTPUT_DIR" "https://www.open-epg.com/files/$filename"
			sleep 1
		fi
		gzip -df "$filepath"
	done

	find "$OUTPUT_DIR" -maxdepth 1 -name "${country}*" -type f -empty -delete
}

function download_epg_share_epg() {
	local url=$1
    local filename
    local filepath

    filename=$(basename "$url")
    filepath="$OUTPUT_DIR/$filename"

	# Remove empty files
	find "$OUTPUT_DIR" -maxdepth 1 -name "$filename" -type f -empty -delete
	if [[ ! -f "$filepath" ]]; then
		wget -P "$OUTPUT_DIR" "$url"
		sleep 1
	fi
	gzip -df "$filepath"
	find "$OUTPUT_DIR" -maxdepth 1 -name "$filename" -type f -empty -delete
}

# Loop through countries
for country in ireland unitedstates unitedkingdom; do
	download_open_epg "$country"
done

for url in "https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz" "https://epgshare01.online/epgshare01/epg_ripper_IE1.xml.gz" "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"; do
	download_epg_share_epg "$url"
done
