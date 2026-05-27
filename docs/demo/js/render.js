// Theme colors
const THEME = {
    canvasBg: '#ffffff',
    gridLine: '#e4e6eb',
    pieceBorder: '#ffffff',
    highlight: '#1c1e21',
    labelFill: '#1c1e21',
    labelStroke: '#ffffff',
    baseLabelFill: '#1c1e21',
    baseLabelStroke: '#ffffff',
    heightIndicator: '#E6193B'
};

class BoardRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.cellSize = 30;
        this.highlightedPiece = null;
    }

    render(board) {
        const ctx = this.ctx;
        const cellSize = this.cellSize;

        // Clear canvas
        ctx.fillStyle = THEME.canvasBg;
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw grid lines (background)
        ctx.strokeStyle = THEME.gridLine;
        ctx.lineWidth = 1;
        for (let x = 0; x <= board.width; x++) {
            ctx.beginPath();
            ctx.moveTo(x * cellSize, 0);
            ctx.lineTo(x * cellSize, board.height * cellSize);
            ctx.stroke();
        }
        for (let y = 0; y <= board.height; y++) {
            ctx.beginPath();
            ctx.moveTo(0, y * cellSize);
            ctx.lineTo(board.width * cellSize, y * cellSize);
            ctx.stroke();
        }

        // Helper to check if adjacent cell belongs to same piece
        const isSamePiece = (x, y, pieceId) => {
            if (x < 0 || x >= board.width || y < 0 || y >= board.height) return false;
            const cell = board.grid[y][x];
            return cell && cell.pieceId === pieceId;
        };

        // Draw cells as connected pieces (y=0 is bottom, so we flip for display)
        for (let y = 0; y < board.height; y++) {
            for (let x = 0; x < board.width; x++) {
                const cell = board.grid[y][x];
                if (cell) {
                    const displayY = (board.height - 1 - y) * cellSize;
                    const displayX = x * cellSize;

                    // Fill with piece color (full cell, no gap)
                    ctx.fillStyle = cell.color;
                    ctx.fillRect(displayX, displayY, cellSize, cellSize);

                    // Draw borders only on edges not adjacent to same piece
                    ctx.strokeStyle = THEME.pieceBorder;
                    ctx.lineWidth = 2;

                    // Top edge (check y+1 in grid = above in display)
                    if (!isSamePiece(x, y + 1, cell.pieceId)) {
                        ctx.beginPath();
                        ctx.moveTo(displayX, displayY);
                        ctx.lineTo(displayX + cellSize, displayY);
                        ctx.stroke();
                    }
                    // Bottom edge
                    if (!isSamePiece(x, y - 1, cell.pieceId)) {
                        ctx.beginPath();
                        ctx.moveTo(displayX, displayY + cellSize);
                        ctx.lineTo(displayX + cellSize, displayY + cellSize);
                        ctx.stroke();
                    }
                    // Left edge
                    if (!isSamePiece(x - 1, y, cell.pieceId)) {
                        ctx.beginPath();
                        ctx.moveTo(displayX, displayY);
                        ctx.lineTo(displayX, displayY + cellSize);
                        ctx.stroke();
                    }
                    // Right edge
                    if (!isSamePiece(x + 1, y, cell.pieceId)) {
                        ctx.beginPath();
                        ctx.moveTo(displayX + cellSize, displayY);
                        ctx.lineTo(displayX + cellSize, displayY + cellSize);
                        ctx.stroke();
                    }

                    // Highlight if this is the highlighted piece
                    if (cell.pieceId === this.highlightedPiece) {
                        ctx.strokeStyle = THEME.highlight;
                        ctx.lineWidth = 3;
                        ctx.strokeRect(displayX + 2, displayY + 2, cellSize - 4, cellSize - 4);
                    }
                }
            }
        }

        // Draw height indicator
        const height = board.getHeight();
        if (height > 0) {
            const indicatorY = (board.height - height) * cellSize;
            ctx.strokeStyle = THEME.heightIndicator;
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(0, indicatorY);
            ctx.lineTo(board.width * cellSize, indicatorY);
            ctx.stroke();
            ctx.setLineDash([]);

            // Height label
            const heightFontSize = Math.max(9, Math.floor(cellSize * 0.4));
            ctx.fillStyle = THEME.heightIndicator;
            ctx.font = `${heightFontSize}px sans-serif`;
            ctx.fillText(`h=${height}`, board.width * cellSize + 5, indicatorY + 4);
        }
    }

    setHighlightedPiece(pieceId) {
        this.highlightedPiece = pieceId;
    }
}

class ShapleyBoardRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.cellSize = 30;
    }

    // Parse hex color to RGB
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : { r: 128, g: 128, b: 128 };
    }

    render(board, contributions) {
        const ctx = this.ctx;
        const cellSize = this.cellSize;

        // Clear canvas
        ctx.fillStyle = THEME.canvasBg;
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw grid lines (background)
        ctx.strokeStyle = THEME.gridLine;
        ctx.lineWidth = 1;
        for (let x = 0; x <= board.width; x++) {
            ctx.beginPath();
            ctx.moveTo(x * cellSize, 0);
            ctx.lineTo(x * cellSize, board.height * cellSize);
            ctx.stroke();
        }
        for (let y = 0; y <= board.height; y++) {
            ctx.beginPath();
            ctx.moveTo(0, y * cellSize);
            ctx.lineTo(board.width * cellSize, y * cellSize);
            ctx.stroke();
        }

        // Helper to check if adjacent cell belongs to same piece
        const isSamePiece = (x, y, pieceId) => {
            if (x < 0 || x >= board.width || y < 0 || y >= board.height) return false;
            const cell = board.grid[y][x];
            return cell && cell.pieceId === pieceId;
        };

        // Calculate max contribution for scaling opacity
        const pieceIds = board.getPieceIds();
        let maxContrib = 0;
        for (const id of pieceIds) {
            const contrib = contributions.get(id) || 0;
            maxContrib = Math.max(maxContrib, Math.abs(contrib));
        }
        maxContrib = Math.max(maxContrib, 0.1); // Avoid division by zero

        // Track piece centers for label rendering
        const pieceCenters = new Map(); // pieceId -> { sumX, sumY, count }

        // Draw cells with opacity based on contribution
        for (let y = 0; y < board.height; y++) {
            for (let x = 0; x < board.width; x++) {
                const cell = board.grid[y][x];
                if (cell) {
                    const displayY = (board.height - 1 - y) * cellSize;
                    const displayX = x * cellSize;

                    // Track center for this piece
                    if (!pieceCenters.has(cell.pieceId)) {
                        pieceCenters.set(cell.pieceId, { sumX: 0, sumY: 0, count: 0 });
                    }
                    const center = pieceCenters.get(cell.pieceId);
                    center.sumX += displayX + cellSize / 2;
                    center.sumY += displayY + cellSize / 2;
                    center.count++;

                    // Get contribution for this piece
                    const contrib = contributions.get(cell.pieceId) || 0;
                    // Map contribution to opacity (0.15 to 1.0)
                    const opacity = 0.15 + (contrib / maxContrib) * 0.85;

                    // Parse color and apply opacity
                    const rgb = this.hexToRgb(cell.color);
                    ctx.fillStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${opacity})`;
                    ctx.fillRect(displayX, displayY, cellSize, cellSize);

                    // Draw borders only on edges not adjacent to same piece
                    ctx.strokeStyle = THEME.pieceBorder;
                    ctx.lineWidth = 2;

                    // Top edge
                    if (!isSamePiece(x, y + 1, cell.pieceId)) {
                        ctx.beginPath();
                        ctx.moveTo(displayX, displayY);
                        ctx.lineTo(displayX + cellSize, displayY);
                        ctx.stroke();
                    }
                    // Bottom edge
                    if (!isSamePiece(x, y - 1, cell.pieceId)) {
                        ctx.beginPath();
                        ctx.moveTo(displayX, displayY + cellSize);
                        ctx.lineTo(displayX + cellSize, displayY + cellSize);
                        ctx.stroke();
                    }
                    // Left edge
                    if (!isSamePiece(x - 1, y, cell.pieceId)) {
                        ctx.beginPath();
                        ctx.moveTo(displayX, displayY);
                        ctx.lineTo(displayX, displayY + cellSize);
                        ctx.stroke();
                    }
                    // Right edge
                    if (!isSamePiece(x + 1, y, cell.pieceId)) {
                        ctx.beginPath();
                        ctx.moveTo(displayX + cellSize, displayY);
                        ctx.lineTo(displayX + cellSize, displayY + cellSize);
                        ctx.stroke();
                    }
                }
            }
        }

        // Draw contribution labels at piece centers
        const contribFontSize = Math.max(8, Math.floor(cellSize * 0.37));
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        for (const [pieceId, center] of pieceCenters) {
            const contrib = contributions.get(pieceId) || 0;
            if (contrib <= 0) continue;
            const label = contrib.toFixed(1);
            const x = center.sumX / center.count;
            const y = center.sumY / center.count;
            ctx.font = `bold ${contribFontSize}px sans-serif`;
            ctx.strokeStyle = THEME.labelStroke;
            ctx.lineWidth = 3;
            ctx.strokeText(label, x, y);
            ctx.fillStyle = THEME.labelFill;
            ctx.fillText(label, x, y);
        }
    }
}

window.BoardRenderer = BoardRenderer;
window.ShapleyBoardRenderer = ShapleyBoardRenderer;
