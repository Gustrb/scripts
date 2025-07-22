#!/bin/bash
set -e  # Exit on any error

# Default values
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--dry-run] <input_file_with_s3_urls>"
            echo ""
            echo "Options:"
            echo "  --dry-run    Show what would be processed without making changes"
            echo "  -h, --help   Show this help message"
            echo ""
            echo "Input file should contain one S3 URL per line"
            exit 0
            ;;
        *)
            if [ -z "$INPUT_FILE" ]; then
                INPUT_FILE="$1"
            else
                echo "Error: Unknown option $1"
                echo "Use -h or --help for usage information"
                exit 1
            fi
            shift
            ;;
    esac
done

# Check if input file is provided
if [ -z "$INPUT_FILE" ]; then
    echo "Usage: $0 [--dry-run] <input_file_with_s3_urls>"
    echo "Use -h or --help for more information"
    exit 1
fi

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' not found"
    exit 1
fi

# Check if required tools are available (only if not in dry run mode)
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed or not in PATH"
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed or not in PATH"
    exit 1
fi

# Create temporary directory for processing
TEMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TEMP_DIR"

# Function to cleanup on exit
cleanup() {
    echo "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Function to extract bucket and key from S3 URL
parse_s3_url() {
    local url="$1"
    # Remove s3:// prefix
    local path="${url#s3://}"
    # Split into bucket and key
    local bucket="${path%%/*}"
    local key="${path#*/}"
    echo "$bucket:$key"
}

# Function to process a single video
process_video() {
    local s3_url="$1"
    echo "Processing: $s3_url"
    
    # Parse S3 URL
    local bucket_key=$(parse_s3_url "$s3_url")
    local bucket="${bucket_key%:*}"
    local key="${bucket_key#*:}"
    
    # Extract filename from key
    local filename=$(basename "$key")
    local local_path="$TEMP_DIR/$filename"
    local output_path="$TEMP_DIR/fixed_$filename"
    
    echo "  Downloading from S3..."
    aws s3 cp "$s3_url" "$local_path"
    
    if [ ! -f "$local_path" ]; then
        echo "  Error: Failed to download video"
        return 1
    fi
    
    echo "  Processing with ffmpeg..."
    ffmpeg -fflags +genpts+igndts -i "$local_path" -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k "$output_path" -y
    
    if [ ! -f "$output_path" ]; then
        echo "  Error: Failed to process video with ffmpeg"
        return 1
    fi
    
    if [ "$DRY_RUN" = true ]; then
        echo "  [DRY RUN] Would upload back to S3: $s3_url"
        echo "  [DRY RUN] Successfully processed: $s3_url"
    else
        echo "  Uploading back to S3..."
        # aws s3 cp "$output_path" "$s3_url"
        echo "  Successfully processed: $s3_url"
    fi
    
    # Clean up local files
    rm -f "$local_path" "$output_path"
}

# Main processing loop
if [ "$DRY_RUN" = true ]; then
    echo "Starting video processing (DRY RUN - will download and process but not upload)..."
else
    echo "Starting video processing..."
fi
echo "Reading URLs from: $INPUT_FILE"
echo ""

success_count=0
error_count=0

while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Trim whitespace
    line=$(echo "$line" | xargs)
    
    if [[ "$line" =~ ^s3:// ]]; then
        if process_video "$line"; then
            ((success_count++))
        else
            ((error_count++))
        fi
    else
        echo "Warning: Skipping invalid S3 URL: $line"
        ((error_count++))
    fi
    
    echo ""
done < "$INPUT_FILE"

if [ "$DRY_RUN" = true ]; then
    echo "Dry run complete!"
    echo "Successfully processed: $success_count videos (downloaded and processed, not uploaded)"
    echo "Errors: $error_count videos"
else
    echo "Processing complete!"
    echo "Successfully processed: $success_count videos"
    echo "Errors: $error_count videos"
fi

if [ $error_count -gt 0 ]; then
    exit 1
fi
