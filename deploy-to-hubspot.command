#!/bin/bash
cd "$(dirname "$0")"
echo "Uploading to HubSpot Design Manager..."
hs cms upload ./ yuanta-wealth-theme --account yuanta-wealth
echo ""
echo "Done! Press any key to close."
read -n 1
