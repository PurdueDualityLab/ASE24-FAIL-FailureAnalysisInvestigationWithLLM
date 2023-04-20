#!/bin/bash

# Define arrays of keywords and date ranges
keywords=(
  "software flaw"
  "software fail"
  "software bug"
  "software mistake"
  "software anomaly"
  "software fault"
  "software error"
  "software exception"
  "software crash"
  "software glitch"
  "software defect"
  "software incident"
  "software side effect"
  "software hack"
)

start_years=(2010)
end_years=(2010)
start_months=(01)
end_months=(02)

# Iterate through all combinations of keywords, years, and months
for keyword in "${keywords[@]}"
do
  for (( i=0; i<${#start_years[@]}; i++ ))
  do
    start_year=${start_years[$i]}
    end_year=${end_years[$i]}
    
    for (( j=0; j<${#start_months[@]}; j++ ))
    do
      start_month=${start_months[$j]}
      end_month=${end_months[$j]}
    
      # Execute the command with the current keyword and date range
      docker compose -f local.yml run --rm django python -m failures scrape --sources 'wired.com' 'nytimes.com' --keyword "$keyword" --start-year $start_year --end-year $end_year --start-month $start_month --end-month $end_month
    done
  done
done