export const createArrayOfArrays = (array) => {
  return array?.map((object) => {
    if (!Array.isArray(object)) {
      delete object?.length;
    }
    return Object.values(object);
  });
};

const alchemyRaw = createArrayOfArrays(idleonData?.CauldronInfo) || idleonData?.CauldronInfo;
const liquids = alchemyRaw?.[6]