# what is the length of each obituary (in words)

# you will have to
# 1. join the obituaries across multiple <main> tags and stop them when the next obituary starts
# 2. word count each obituary
# 3. output them as a json with the following format:
# {
#     "obituary_id": "1",
#     "name": "John Doe",
#     "obituary_text": "...",
#     "word_count": 100
# }

# identify where the obituary starts and ends
# regex to find: 1913 - 2010 OR **1938-2017** or 1948-2010 or Dave Cuthbertson1948 - 2019

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from loguru import logger

if __name__ == "__main__":
    # get the path to the markdown files
    markdown_dir = Path("./data/AlpineJournalObituary")
    assert markdown_dir.exists(), f"Directory {markdown_dir} does not exist"
    markdown_file = markdown_dir / "AlpineJournalObituary.md"
    assert markdown_file.exists(), f"File {markdown_file} does not exist"

    # read the markdown file
    with open(markdown_file, "r") as f:
        markdown_text = f.read()

    # extract only the text between <main> tags
    main_text_parts = re.findall(r"<main>(.*?)</main>", markdown_text, re.DOTALL)

    # Join all the main text parts into a single string
    main_text = "\n".join(main_text_parts)

    # identify where the obituary starts and ends
    # regex to find: 1913 - 2010 OR **1938-2017** or 1948-2010 or Dave Cuthbertson1948 - 2019
    obituary_regex = re.compile(r"\d{4}\s*-\s*\d{4}|\*\*\d{4}-\d{4}\*\*")
    date_matches = list(obituary_regex.finditer(main_text))
    logger.info(f"Found {len(date_matches)} obituary date ranges")

    # get the text BEFORE the found regex to the start of the line which contains the name:
    #  **Robert (Bob) Alexander Creswell 1948 - 2010
    #  and drop the * characters if they exist

    # Process the obituaries
    obituaries = []

    # If we found obituary ranges, process them
    if date_matches:
        # Find the start of each line containing a date
        line_starts = []
        for match in date_matches:
            # Find the start of the line containing this date
            line_start = main_text.rfind("\n", 0, match.start())
            if line_start == -1:
                line_start = 0
            else:
                line_start += 1  # Skip the newline character
            line_starts.append(line_start)

        # Add the end of the text as the final boundary
        boundaries = [0] + line_starts + [len(main_text)]

        # Process each obituary
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]

            obituary_text = main_text[start:end].strip()

            # Extract name using a more precise approach
            # Look for the line containing the date pattern
            date_match = re.search(
                r"\d{4}\s*-\s*\d{4}|\*\*\d{4}-\d{4}\*\*", obituary_text
            )
            if date_match:
                # Get the line containing the date
                line_start = obituary_text.rfind("\n", 0, date_match.start())
                if line_start == -1:
                    line_start = 0
                else:
                    line_start += 1  # Skip the newline character

                line_end = obituary_text.find("\n", date_match.end())
                if line_end == -1:
                    line_end = len(obituary_text)

                date_line = obituary_text[line_start:line_end].strip()

                # Check if the name is on the previous line
                prev_line_start = obituary_text.rfind("\n", 0, line_start)
                if prev_line_start == -1:
                    prev_line_start = 0
                else:
                    prev_line_start += 1  # Skip the newline character

                prev_line = obituary_text[prev_line_start:line_start].strip()

                # If the previous line contains asterisks and no date pattern, it's likely the name
                if re.search(r"\*+", prev_line) and not re.search(
                    r"\d{4}\s*-\s*\d{4}|\*\*\d{4}-\d{4}\*\*", prev_line
                ):
                    name_line = prev_line
                else:
                    # Otherwise, use the date line and extract name from it
                    name_line = date_line

                # Remove asterisks and extract the name (everything before the date)
                name = re.sub(r"\*+", "", name_line).strip()
                name = re.sub(
                    r"\d{4}\s*-\s*\d{4}.*$|\*\*\d{4}-\d{4}\*\*.*$", "", name
                ).strip()

                # If name is empty after processing, try to get it from the previous line
                if not name and prev_line:
                    name = re.sub(r"\*+", "", prev_line).strip()
            else:
                # Fallback if no date is found
                name = "Unknown"

            # Count words
            word_count = len(obituary_text.split())

            obituary = {
                "obituary_id": str(i + 1),
                "name": name,
                "obituary_text": obituary_text,
                "word_count": word_count,
            }

            obituaries.append(obituary)

    # Output the results
    logger.info(f"Processed {len(obituaries)} obituaries")

    # Save to JSON file
    output_file = markdown_dir / "obituaries.json"
    with open(output_file, "w") as f:
        json.dump(obituaries, f, indent=2)

    logger.success(f"Results saved to {output_file}")

    # Read as dataframe
    df = pd.read_json(output_file)

    # remove the first row
    df = df.iloc[1:]

    # create a histogram of the word count with key stats shown below:
    # mean, median, min, max, 5%le, 95%le
    plt.figure(figsize=(12, 8))

    # Create histogram
    n, bins, patches = plt.hist(
        df["word_count"], bins=20, alpha=0.7, color="skyblue", edgecolor="black"
    )

    # Calculate statistics
    mean = df["word_count"].mean()
    median = df["word_count"].median()
    min_val = df["word_count"].min()
    max_val = df["word_count"].max()
    percentile_5 = df["word_count"].quantile(0.05)
    percentile_95 = df["word_count"].quantile(0.95)

    # Add vertical lines for statistics
    plt.axvline(
        mean, color="red", linestyle="dashed", linewidth=2, label=f"Mean: {mean:.1f}"
    )
    plt.axvline(
        median,
        color="green",
        linestyle="dashed",
        linewidth=2,
        label=f"Median: {median:.1f}",
    )
    plt.axvline(
        min_val,
        color="purple",
        linestyle="dashed",
        linewidth=2,
        label=f"Min: {min_val:.1f}",
    )
    plt.axvline(
        max_val,
        color="orange",
        linestyle="dashed",
        linewidth=2,
        label=f"Max: {max_val:.1f}",
    )
    plt.axvline(
        percentile_5,
        color="brown",
        linestyle="dashed",
        linewidth=2,
        label=f"5th Percentile: {percentile_5:.1f}",
    )
    plt.axvline(
        percentile_95,
        color="blue",
        linestyle="dashed",
        linewidth=2,
        label=f"95th Percentile: {percentile_95:.1f}",
    )

    # Add labels and title
    plt.xlabel("Word Count")
    plt.ylabel("Frequency")
    plt.title("Histogram of Obituary Word Counts")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Add text box with statistics
    stats_text = f"Statistics:\nMean: {mean:.1f}\nMedian: {median:.1f}\nMin: {min_val:.1f}\nMax: {max_val:.1f}\n5th Percentile: {percentile_5:.1f}\n95th Percentile: {percentile_95:.1f}"
    plt.text(
        0.95,
        0.95,
        stats_text,
        transform=plt.gca().transAxes,
        fontsize=10,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    # Save the plot
    plot_file = markdown_dir / "obituary_word_count_histogram.png"
    plt.savefig(plot_file, dpi=300, bbox_inches="tight")
    logger.success(f"Histogram saved to {plot_file}")

    # Show the plot
    plt.tight_layout()
    plt.show()
