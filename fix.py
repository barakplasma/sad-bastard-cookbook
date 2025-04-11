import os
import re
import argparse
import sys # Import sys to exit gracefully on error

# Regex to find the first H2 header and capture its content
# ^##\s+ : Starts with '##' followed by one or more spaces
# (.*?)  : Captures the title (non-greedily)
# \s*    : Matches optional whitespace before the potential brace
# }?     : Matches an optional closing brace '}' literally
# \s*    : Matches optional trailing whitespace
# $      : End of the line
HEADER_RE = re.compile(r"^##\s+(.*?)\s*}?\s*$", re.IGNORECASE)

# Regex to check for existing Zola front matter
FRONT_MATTER_RE = re.compile(r"^\s*\+\+\+\s*$")

def process_markdown_file(filepath):
    """
    Reads a markdown file, finds the first H2 header, converts it to
    Zola front matter, removes the original header, and saves the file.
    """
    try:
        # Read with universal newline mode to handle different line endings
        with open(filepath, 'r', encoding='utf-8', newline='') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return False # Indicate failure

    if not lines:
        print(f"Skipping empty file: {filepath}")
        return True # Indicate success (nothing to do)

    # Check if front matter already exists
    if FRONT_MATTER_RE.match(lines[0]):
        print(f"Skipping file with existing front matter: {filepath}")
        return True # Indicate success (already done)

    found_header = False
    title = None
    header_line_index = -1

    # Find the first H2 header
    for i, line in enumerate(lines):
        # Strip trailing newline/whitespace for reliable regex matching at end of line ($)
        match = HEADER_RE.match(line.rstrip())
        if match:
            # Extract title, strip whitespace, and escape double quotes
            title = match.group(1).strip().replace('"', '\\"')
            header_line_index = i
            found_header = True
            print(f"Found title '{title}' in {filepath}")
            break # Stop after finding the first H2

    if not found_header:
        print(f"Warning: No matching H2 header found in {filepath}. Skipping.")
        return True # Indicate success (no header to process)

    # Create Zola front matter - ensure trailing newline
    front_matter = f"+++\ntitle = \"{title}\"\n+++\n\n"

    # Remove the original header line
    original_header_line = lines.pop(header_line_index)

    # Ensure there's exactly one blank line after front matter if content exists
    # Remove leading blank lines from the remaining content if they exist
    while lines and lines[0].strip() == "":
         lines.pop(0)

    # Combine front matter and the rest of the content
    new_content = front_matter + "".join(lines)

    # Write the modified content back to the file
    try:
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(new_content)
        print(f"Successfully processed and updated: {filepath}")
        return True # Indicate success
    except Exception as e:
        print(f"Error writing file {filepath}: {e}")
        return False # Indicate failure


def main():
    parser = argparse.ArgumentParser(
        description="Convert first H2 Markdown header to Zola front matter."
    )
    # --- THIS IS THE CORRECTED LINE ---
    parser.add_argument(
        "directory",
        help="The directory containing Markdown files to process."
    )
    # --- END CORRECTION ---
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan files and report changes without actually modifying them."
    )

    args = parser.parse_args()

    target_dir = args.directory

    if not os.path.isdir(target_dir):
        print(f"Error: Directory '{target_dir}' not found.", file=sys.stderr)
        sys.exit(1) # Exit with error code

    print(f"Processing Markdown files in: {target_dir}")
    if args.dry_run:
        print("--- DRY RUN MODE: No files will be modified. ---")
    else:
        print("--- IMPORTANT: This script modifies files in place! ---")
        print("--- Make sure you have a backup before proceeding. ---")
        try:
            confirm = input("Continue? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Operation cancelled.")
                sys.exit(0)
        except EOFError: # Handle non-interactive environments
             print("Warning: Running non-interactively. Assuming 'yes'. Ensure backups exist.", file=sys.stderr)


    processed_count = 0
    skipped_count = 0
    error_count = 0

    for root, _, files in os.walk(target_dir):
        for filename in files:
            if filename.lower().endswith('.md'):
                filepath = os.path.join(root, filename)
                if args.dry_run:
                    # Simulate processing in dry run
                    try:
                        with open(filepath, 'r', encoding='utf-8', newline='') as f:
                             lines = f.readlines()
                        if not lines: continue # Skip empty
                        if FRONT_MATTER_RE.match(lines[0]): continue # Skip existing front matter

                        found_header = False
                        for line in lines:
                             match = HEADER_RE.match(line.rstrip())
                             if match:
                                 title = match.group(1).strip().replace('"', '\\"')
                                 print(f"[Dry Run] Would find title '{title}' and add front matter to: {filepath}")
                                 processed_count += 1
                                 found_header = True
                                 break
                        if not found_header:
                             print(f"[Dry Run] No matching H2 header found in: {filepath}")
                             skipped_count += 1

                    except Exception as e:
                        print(f"[Dry Run] Error reading file {filepath}: {e}")
                        error_count += 1
                else:
                    # Actual processing
                    success = process_markdown_file(filepath)
                    if success:
                        # Further check if it was skipped or processed based on output
                        # (This is a bit indirect, could improve process_markdown_file return values)
                         processed_count +=1 # Count all non-error attempts for simplicity here
                    else:
                         error_count +=1


    print("\n--- Processing Summary ---")
    if args.dry_run:
        print(f"Files that would be processed: {processed_count}")
        print(f"Files skipped (no header/empty): {skipped_count}")
        print(f"Files with reading errors: {error_count}")
    else:
         # In live run, process_markdown_file prints details, so just give counts
        print(f"Files processed or skipped (see logs above): {processed_count}")
        print(f"Files with processing errors: {error_count}")
    print("Processing complete.")

if __name__ == "__main__":
    main()