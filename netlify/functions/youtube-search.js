// netlify/functions/youtube-search.js

const SEARCH_URL = "https://www.googleapis.com/youtube/v3/search";
const VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos";

async function httpGet(url, params) {
  const query = new URLSearchParams(params || {}).toString();
  const fullUrl = `${url}?${query}`;

  const resp = await fetch(fullUrl);
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`HTTP ${resp.status} ${resp.statusText}: ${text}`);
  }
  return resp.json();
}

async function searchVideos(apiKey, query, limit = 5, order = "relevance") {
  const params = {
    part: "snippet",
    q: query,
    type: "video",
    maxResults: limit,
    order,
    key: apiKey,
  };
  const data = await httpGet(SEARCH_URL, params);
  return data.items || [];
}

async function getVideoDetails(apiKey, videoIds) {
  if (!videoIds || videoIds.length === 0) return [];
  const params = {
    part: "snippet,statistics,contentDetails",
    id: videoIds.join(","),
    key: apiKey,
  };
  const data = await httpGet(VIDEOS_URL, params);
  return data.items || [];
}

exports.handler = async (event, context) => {
  const headers = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
  };

  const API_KEY = process.env.YOUTUBE_API_KEY;
  if (!API_KEY) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: "YOUTUBE_API_KEY not configured" }),
    };
  }

  try {
    const params = event.queryStringParameters || {};
    const query = params.q;
    const limitParam = params.limit;
    const order = params.order || "relevance";

    if (!query) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: "Missing 'q' query parameter" }),
      };
    }

    let limit = 5;
    if (limitParam) {
      const parsed = parseInt(limitParam, 10);
      if (!Number.isNaN(parsed) && parsed > 0) {
        limit = parsed;
      }
    }

    const searchItems = await searchVideos(API_KEY, query, limit, order);

    const videoIds = searchItems
      .map((item) => {
        const idObj = item.id || {};
        if (idObj.kind === "youtube#video") {
          return idObj.videoId;
        }
        return null;
      })
      .filter(Boolean);

    if (videoIds.length === 0) {
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({ results: [] }),
      };
    }

    const details = await getVideoDetails(API_KEY, videoIds);
    const detailsById = {};
    details.forEach((d) => {
      detailsById[d.id] = d;
    });

    const results = [];

    searchItems.forEach((item) => {
      const idObj = item.id || {};
      const vid = idObj.videoId;
      if (!vid) return;

      const searchSnippet = item.snippet || {};
      const full = detailsById[vid] || {};
      const fullSnippet = full.snippet || searchSnippet;

      const title = fullSnippet.title || searchSnippet.title || "Untitled video";
      const channelTitle =
        fullSnippet.channelTitle || searchSnippet.channelTitle || "";
      const publishedAt =
        fullSnippet.publishedAt || searchSnippet.publishedAt || "";

      const stats = full.statistics || {};
      const viewCount = stats.viewCount || "";
      const likeCount = stats.likeCount || "";

      const thumbnails =
        fullSnippet.thumbnails || searchSnippet.thumbnails || {};
      const thumbnailUrl =
        (thumbnails.medium && thumbnails.medium.url) ||
        (thumbnails.high && thumbnails.high.url) ||
        (thumbnails.default && thumbnails.default.url) ||
        `https://i.ytimg.com/vi/${vid}/hqdefault.jpg`;

      results.push({
        videoId: vid,
        title,
        channelTitle,
        publishedAt,
        viewCount,
        likeCount,
        thumbnailUrl,
      });
    });

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ results }),
    };
  } catch (err) {
    console.error("ERROR in youtube-search:", err);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: "Internal server error" }),
    };
  }
};
