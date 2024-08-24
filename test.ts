const rawFarmingPlot = tryToParse(idleonData?.FarmPlot);
const rawFarmingRanks = tryToParse(idleonData?.FarmRank);
const [farmingRanks, ranksProgress, upgradesLevels] = rawFarmingRanks || [];

const plot = rawFarmingPlot?.map(([seedType, progress, cropType, isLocked, cropQuantity, currentOG, cropProgress]: number[], index: number) => {
  const type = Math.round(const_seedInfo?.[seedType]?.cropIdMin + cropType);
  const growthReq = 14400 * Math.pow(1.5, seedType);
  const rank = farmingRanks?.[index];
  const rankProgress = ranksProgress?.[index];
  const rankRequirement = (7 * rank + 25 * Math.floor(rank / 5) + 10) * Math.pow(1.11, rank);
  return {
    rank,
    rankProgress,
    rankRequirement,
    seedType,
    cropType: type,
    cropQuantity,
    cropProgress,
    progress,
    growthReq,
    isLocked,
    currentOG,
    cropRawName: `FarmCrop${type}.png`,
    seedRawName: `Seed_${seedType}.png`
  }
})