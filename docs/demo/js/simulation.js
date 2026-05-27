// Fisher-Yates shuffle with seeded random
function shuffleArray(array, rand) {
    const result = [...array];
    for (let i = result.length - 1; i > 0; i--) {
        const j = Math.floor(rand() * (i + 1));
        [result[i], result[j]] = [result[j], result[i]];
    }
    return result;
}

class ShapleySimulation {
    constructor(originalBoard, seed) {
        this.originalBoard = originalBoard;
        this.seed = seed;
        this.rand = mulberry32(seed);

        // Track contributions per piece
        this.contributions = new Map(); // pieceId -> { total: number, count: number }
        this.pieceIds = originalBoard.getPieceIds();

        for (const id of this.pieceIds) {
            this.contributions.set(id, { total: 0, count: 0 });
        }

        this.iterationCount = 0;
        this.currentIteration = null;
    }

    // Run a single iteration and return step-by-step data for visualization
    *runIteration() {
        this.iterationCount++;
        const board = this.originalBoard.clone();
        const permutation = shuffleArray(this.pieceIds, this.rand);

        let currentHeight = board.getHeight();

        yield {
            type: 'start',
            iteration: this.iterationCount,
            board: board.clone(),
            height: currentHeight,
            permutation: [...permutation]
        };

        for (let i = 0; i < permutation.length; i++) {
            const pieceId = permutation[i];
            const heightBefore = currentHeight;

            // Remove the piece
            board.removePiece(pieceId);

            // Apply gravity
            board.applyGravity();

            // Calculate new height
            const heightAfter = board.getHeight();
            currentHeight = heightAfter;

            // Marginal contribution = how much height was reduced by removing this piece
            const contribution = heightBefore - heightAfter;

            // Accumulate
            const pieceContrib = this.contributions.get(pieceId);
            pieceContrib.total += contribution;
            pieceContrib.count++;

            yield {
                type: 'step',
                iteration: this.iterationCount,
                stepIndex: i,
                pieceId,
                heightBefore,
                heightAfter,
                contribution,
                board: board.clone(),
                currentContributions: this.getAverageContributions()
            };
        }

        yield {
            type: 'end',
            iteration: this.iterationCount,
            contributions: this.getAverageContributions()
        };
    }

    // Run multiple iterations without yielding intermediate steps
    runIterations(count) {
        for (let i = 0; i < count; i++) {
            const board = this.originalBoard.clone();
            const permutation = shuffleArray(this.pieceIds, this.rand);

            let currentHeight = board.getHeight();

            for (const pieceId of permutation) {
                const heightBefore = currentHeight;

                board.removePiece(pieceId);
                board.applyGravity();

                const heightAfter = board.getHeight();
                currentHeight = heightAfter;

                const contribution = heightBefore - heightAfter;

                const pieceContrib = this.contributions.get(pieceId);
                pieceContrib.total += contribution;
                pieceContrib.count++;
            }

            this.iterationCount++;
        }

        return this.getAverageContributions();
    }

    getAverageContributions() {
        const result = new Map();
        for (const [id, { total, count }] of this.contributions) {
            result.set(id, count > 0 ? total / count : 0);
        }
        return result;
    }

    getTotalIterations() {
        return this.iterationCount;
    }

    reset() {
        this.rand = mulberry32(this.seed);
        for (const id of this.pieceIds) {
            this.contributions.set(id, { total: 0, count: 0 });
        }
        this.iterationCount = 0;
    }
}

// Export
window.ShapleySimulation = ShapleySimulation;
