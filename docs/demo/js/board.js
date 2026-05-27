// Seeded PRNG - Mulberry32
function mulberry32(seed) {
    return function() {
        let t = seed += 0x6D2B79F5;
        t = Math.imul(t ^ t >>> 15, t | 1);
        t ^= t + Math.imul(t ^ t >>> 7, t | 61);
        return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
}

// Piece colors
const PIECE_SHAPES = {
    I: { cells: [[0,0], [1,0], [2,0], [3,0]], color: '#FA7DC8' },  // Pink
    O: { cells: [[0,0], [1,0], [0,1], [1,1]], color: '#F0AA19' },  // Yellow
    T: { cells: [[0,0], [1,0], [2,0], [1,1]], color: '#8773FF' },  // Purple
    S: { cells: [[1,0], [2,0], [0,1], [1,1]], color: '#13BE19' },  // Green
    Z: { cells: [[0,0], [1,0], [1,1], [2,1]], color: '#E6193B' },  // Red
    J: { cells: [[0,0], [0,1], [1,1], [2,1]], color: '#00C8F0' },  // Light blue
    L: { cells: [[2,0], [0,1], [1,1], [2,1]], color: '#FA8719' }   // Orange
};

const PIECE_TYPES = Object.keys(PIECE_SHAPES);

// Rotate piece cells by 0, 90, 180, or 270 degrees clockwise
function rotateCells(cells, rotation) {
    if (rotation === 0) return cells;

    // Apply rotation transformation
    let rotated = cells.map(([x, y]) => {
        switch (rotation) {
            case 1: return [y, -x];      // 90° clockwise
            case 2: return [-x, -y];     // 180°
            case 3: return [-y, x];      // 270° clockwise
            default: return [x, y];
        }
    });

    // Normalize to positive coordinates (shift to 0,0 origin)
    const minX = Math.min(...rotated.map(c => c[0]));
    const minY = Math.min(...rotated.map(c => c[1]));
    return rotated.map(([x, y]) => [x - minX, y - minY]);
}

class Board {
    constructor(width = 10, height = 20) {
        this.width = width;
        this.height = height;
        this.grid = [];
        this.pieces = new Map(); // pieceId -> { type, color, cells: [{x, y}] }
        this.nextPieceId = 0;
        this.clear();
    }

    clear() {
        this.grid = [];
        for (let y = 0; y < this.height; y++) {
            this.grid.push(new Array(this.width).fill(null));
        }
        this.pieces.clear();
        this.nextPieceId = 0;
    }

    clone() {
        const newBoard = new Board(this.width, this.height);
        for (let y = 0; y < this.height; y++) {
            for (let x = 0; x < this.width; x++) {
                if (this.grid[y][x]) {
                    newBoard.grid[y][x] = { ...this.grid[y][x] };
                }
            }
        }
        for (const [id, piece] of this.pieces) {
            newBoard.pieces.set(id, {
                type: piece.type,
                color: piece.color,
                cells: piece.cells.map(c => ({ ...c }))
            });
        }
        newBoard.nextPieceId = this.nextPieceId;
        return newBoard;
    }

    getHeight() {
        for (let y = this.height - 1; y >= 0; y--) {
            for (let x = 0; x < this.width; x++) {
                if (this.grid[y][x] !== null) {
                    return y + 1;
                }
            }
        }
        return 0;
    }

    canPlacePiece(type, baseX, baseY, rotation = 0) {
        const shape = PIECE_SHAPES[type];
        const cells = rotateCells(shape.cells, rotation);
        for (const [dx, dy] of cells) {
            const x = baseX + dx;
            const y = baseY + dy;
            if (x < 0 || x >= this.width || y < 0 || y >= this.height) {
                return false;
            }
            if (this.grid[y][x] !== null) {
                return false;
            }
        }
        return true;
    }

    placePiece(type, baseX, baseY, rotation = 0) {
        if (!this.canPlacePiece(type, baseX, baseY, rotation)) {
            return null;
        }

        const shape = PIECE_SHAPES[type];
        const rotatedCells = rotateCells(shape.cells, rotation);
        const pieceId = this.nextPieceId++;
        const cells = [];

        for (const [dx, dy] of rotatedCells) {
            const x = baseX + dx;
            const y = baseY + dy;
            this.grid[y][x] = { pieceId, color: shape.color };
            cells.push({ x, y });
        }

        this.pieces.set(pieceId, {
            type,
            color: shape.color,
            cells
        });

        return pieceId;
    }

    removePiece(pieceId) {
        const piece = this.pieces.get(pieceId);
        if (!piece) return false;

        for (const { x, y } of piece.cells) {
            this.grid[y][x] = null;
        }
        this.pieces.delete(pieceId);
        return true;
    }

    // Drop a single piece as far as it can go
    dropPiece(pieceId) {
        const piece = this.pieces.get(pieceId);
        if (!piece) return 0;

        // Find the minimum drop distance for all cells
        let minDrop = this.height;
        for (const { x, y } of piece.cells) {
            let drop = 0;
            for (let testY = y - 1; testY >= 0; testY--) {
                const cell = this.grid[testY][x];
                if (cell !== null && cell.pieceId !== pieceId) {
                    break;
                }
                drop++;
            }
            // Also check for bottom of board
            drop = Math.min(drop, y);
            minDrop = Math.min(minDrop, drop);
        }

        if (minDrop === 0) return 0;

        // Remove piece from current positions
        for (const { x, y } of piece.cells) {
            this.grid[y][x] = null;
        }

        // Place piece at new positions
        for (const cell of piece.cells) {
            cell.y -= minDrop;
            this.grid[cell.y][cell.x] = { pieceId, color: piece.color };
        }

        return minDrop;
    }

    applyGravity() {
        // Sort pieces by their lowest cell (bottom-up processing)
        const pieceIds = [...this.pieces.keys()];
        pieceIds.sort((a, b) => {
            const pieceA = this.pieces.get(a);
            const pieceB = this.pieces.get(b);
            const minYA = Math.min(...pieceA.cells.map(c => c.y));
            const minYB = Math.min(...pieceB.cells.map(c => c.y));
            return minYA - minYB;
        });

        let totalDropped = 0;
        let changed = true;
        while (changed) {
            changed = false;
            for (const pieceId of pieceIds) {
                const dropped = this.dropPiece(pieceId);
                if (dropped > 0) {
                    totalDropped += dropped;
                    changed = true;
                }
            }
        }
        return totalDropped;
    }

    getPieceIds() {
        return [...this.pieces.keys()];
    }

    getPiece(pieceId) {
        return this.pieces.get(pieceId);
    }

    // Generate a mostly-filled board
    static generate(seed, width = 10, fillRatio = 0.7) {
        const rand = mulberry32(seed);
        const board = new Board(width, 20);

        // Place a full-width base block in the bottom row
        const basePieceId = board.nextPieceId++;
        const baseColor = '#00D2BE'; // Teal
        const baseCells = [];
        for (let x = 0; x < width; x++) {
            board.grid[0][x] = { pieceId: basePieceId, color: baseColor };
            baseCells.push({ x, y: 0 });
        }
        board.pieces.set(basePieceId, {
            type: 'BASE',
            color: baseColor,
            cells: baseCells
        });

        // Generate other pieces only above the base (y >= 1)
        let attempts = 0;
        const maxAttempts = 1000;
        const targetCells = Math.floor(board.width * board.height * fillRatio);

        while (board.getFilledCellCount() < targetCells && attempts < maxAttempts) {
            attempts++;

            // Pick a random piece type
            const type = PIECE_TYPES[Math.floor(rand() * PIECE_TYPES.length)];

            // Pick a random rotation (0, 1, 2, or 3 = 0°, 90°, 180°, 270°)
            const rotation = Math.floor(rand() * 4);

            // Try to place it at a random position, but only y >= 1
            const x = Math.floor(rand() * (board.width - 3));
            const y = 1 + Math.floor(rand() * (board.height - 3));

            board.placePiece(type, x, y, rotation);
        }

        // Apply gravity to settle pieces (they'll rest on the base)
        board.applyGravity();

        return board;
    }

    getFilledCellCount() {
        let count = 0;
        for (let y = 0; y < this.height; y++) {
            for (let x = 0; x < this.width; x++) {
                if (this.grid[y][x] !== null) count++;
            }
        }
        return count;
    }

    // Calculate marginal contribution of each piece if removed alone
    calculateMarginalContributions() {
        const contributions = new Map();
        const heightBefore = this.getHeight();

        for (const pieceId of this.getPieceIds()) {
            const testBoard = this.clone();
            testBoard.removePiece(pieceId);
            testBoard.applyGravity();
            const heightAfter = testBoard.getHeight();
            contributions.set(pieceId, heightBefore - heightAfter);
        }

        return contributions;
    }

    // Find critical (load-bearing) pieces by iteratively pruning non-critical ones
    findCriticalPieces() {
        let workingBoard = this.clone();
        const criticalPieces = new Set(this.getPieceIds());

        let changed = true;
        while (changed) {
            changed = false;
            const originalHeight = workingBoard.getHeight();

            for (const pieceId of [...criticalPieces]) {
                const testBoard = workingBoard.clone();
                testBoard.removePiece(pieceId);
                testBoard.applyGravity();

                if (testBoard.getHeight() === originalHeight) {
                    // Not load-bearing - permanently remove
                    workingBoard.removePiece(pieceId);
                    workingBoard.applyGravity();
                    criticalPieces.delete(pieceId);
                    changed = true;
                    break; // Restart since board state changed
                }
            }
        }

        return criticalPieces;
    }

    // Calculate critical path - sequential removal attribution
    // Removes critical pieces bottom-to-top, crediting each for height drop
    // This guarantees sum of contributions = original tower height
    calculateCriticalPath() {
        const contributions = new Map();
        for (const id of this.getPieceIds()) {
            contributions.set(id, 0);
        }

        const height = this.getHeight();
        if (height === 0) return contributions;

        // Phase 1: Find critical pieces
        const criticalPieces = this.findCriticalPieces();

        // Phase 2: Sort critical pieces by lowest row (bottom-up)
        const sortedCritical = [...criticalPieces].sort((a, b) => {
            const pieceA = this.pieces.get(a);
            const pieceB = this.pieces.get(b);
            const minYA = Math.min(...pieceA.cells.map(c => c.y));
            const minYB = Math.min(...pieceB.cells.map(c => c.y));
            return minYA - minYB;
        });

        // Phase 3: Remove pieces sequentially, tracking height drops
        let workingBoard = this.clone();
        // First remove all non-critical pieces
        for (const pieceId of this.getPieceIds()) {
            if (!criticalPieces.has(pieceId)) {
                workingBoard.removePiece(pieceId);
            }
        }
        workingBoard.applyGravity();

        for (const pieceId of sortedCritical) {
            const heightBefore = workingBoard.getHeight();
            workingBoard.removePiece(pieceId);
            workingBoard.applyGravity();
            const heightAfter = workingBoard.getHeight();
            contributions.set(pieceId, heightBefore - heightAfter);
        }

        return contributions;
    }

    // Calculate uniform contributions - distribute 1 unit of blame equally
    // among all distinct pieces present in each row
    calculateUniformContributions() {
        const contributions = new Map();
        for (const id of this.getPieceIds()) {
            contributions.set(id, 0);
        }

        const height = this.getHeight();
        for (let y = 0; y < height; y++) {
            const piecesInRow = new Set();
            for (let x = 0; x < this.width; x++) {
                const cell = this.grid[y][x];
                if (cell) piecesInRow.add(cell.pieceId);
            }
            const share = 1 / piecesInRow.size;
            for (const pieceId of piecesInRow) {
                contributions.set(pieceId, contributions.get(pieceId) + share);
            }
        }

        return contributions;
    }
}

// Export for use in other modules
window.Board = Board;
window.mulberry32 = mulberry32;
window.PIECE_SHAPES = PIECE_SHAPES;
