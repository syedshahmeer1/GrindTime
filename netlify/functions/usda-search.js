// netlify/functions/usda-search.js

const SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search";
const FOOD_URL = "https://api.nal.usda.gov/fdc/v1/food/";

const NUTRIENTS_OF_INTEREST = {
  "Energy": "kcal",
  "Energy, kcal": "kcal",
  "Protein": "g",
  "Carbohydrate, by difference": "g",
  "Total lipid (fat)": "g",
};

async function httpGet(url, params) {
  const query = new URLSearchParams(params || {}).toString();
  const fullUrl = query ? `${url}?${query}` : url;

  const resp = await fetch(fullUrl);
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`HTTP ${resp.status} ${resp.statusText}: ${text}`);
  }
  return resp.json();
}

async function searchFoods(apiKey, query, pageSize = 5, dataType) {
  const params = {
    api_key: apiKey,
    query,
    pageSize,
  };
  if (dataType) {
    // dataType can be comma-separated; FDC accepts repeated params
    dataType.split(",").forEach((dt) => {
      params.dataType = params.dataType || [];
      params.dataType.push(dt.trim());
    });
  }
  return httpGet(SEARCH_URL, params).then((data) => data.foods || []);
}

async function getFoodDetails(apiKey, fdcId) {
  const url = `${FOOD_URL}${fdcId}`;
  return httpGet(url, { api_key: apiKey });
}

function extractFromLabelNutrients(labelNutrients) {
  if (!labelNutrients) return {};

  const out = {};
  if (labelNutrients.calories) {
    out["Energy"] = `${labelNutrients.calories.value} kcal`;
  }
  if (labelNutrients.protein) {
    out["Protein"] = `${labelNutrients.protein.value} g`;
  }
  if (labelNutrients.fat) {
    out["Total lipid (fat)"] = `${labelNutrients.fat.value} g`;
  }
  if (labelNutrients.carbohydrates) {
    out["Carbohydrate, by difference"] = `${labelNutrients.carbohydrates.value} g`;
  }

  const extras = ["sugars", "fiber", "saturatedFat", "transFat", "sodium"];
  extras.forEach((k) => {
    if (labelNutrients[k]) {
      const val = labelNutrients[k].value;
      let unit = "g";
      if (k === "sodium") unit = "mg";
      out[k] = `${val} ${unit}`;
    }
  });

  return out;
}

function extractFromFoodNutrients(foodJson) {
  const out = {};
  const foodNutrients = foodJson.foodNutrients || [];
  foodNutrients.forEach((nutrient) => {
    const name = nutrient.nutrientName;
    const amount = nutrient.value;
    const unit = nutrient.unitName;
    if (Object.prototype.hasOwnProperty.call(NUTRIENTS_OF_INTEREST, name)) {
      out[name] = `${amount} ${unit}`;
    }
  });
  return out;
}

function extractNutrients(detailsJson) {
  // 1) Try branded labelNutrients
  const labelNutrients = detailsJson.labelNutrients;
  const branded = extractFromLabelNutrients(labelNutrients);
  if (Object.keys(branded).length > 0) {
    return branded;
  }

  // 2) Fallback to foodNutrients
  const classic = extractFromFoodNutrients(detailsJson);
  return classic;
}

exports.handler = async (event, context) => {
  const headers = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
  };

  const API_KEY = process.env.USDA_API_KEY;
  if (!API_KEY) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: "USDA_API_KEY not configured" }),
    };
  }

  try {
    const params = event.queryStringParameters || {};
    const query = params.q;
    const limit = params.limit;
    const dataType = params.dataType;

    if (!query) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: "Missing 'q' query parameter" }),
      };
    }

    let pageSize = 5;
    if (limit) {
      const parsed = parseInt(limit, 10);
      if (!Number.isNaN(parsed) && parsed > 0) {
        pageSize = parsed;
      }
    }

    const foods = await searchFoods(API_KEY, query, pageSize, dataType);

    const results = [];
    for (const food of foods) {
      const fdcId = food.fdcId;
      const desc = food.description || "N/A";
      const brand = food.brandOwner || null;
      const dt = food.dataType || "N/A";

      let nutrients = {};
      if (fdcId != null) {
        try {
          const details = await getFoodDetails(API_KEY, fdcId);
          nutrients = extractNutrients(details) || {};
        } catch (e) {
          // If details fetch fails, just leave nutrients empty
          nutrients = {};
        }
      }

      results.push({
        fdcId,
        description: desc,
        brandOwner: brand,
        dataType: dt,
        nutrients,
      });
    }

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ results }),
    };
  } catch (err) {
    console.error("ERROR in usda-search:", err);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: "Internal server error" }),
    };
  }
};
