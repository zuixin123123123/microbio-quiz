package com.microbiology.quiz;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.JavascriptInterface;
import android.view.WindowManager;
import android.os.Build;
import android.graphics.Color;
import android.content.Intent;
import android.net.Uri;
import android.provider.Settings;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.MessageDigest;

public class MainActivity extends Activity {
    private WebView webView;
    private String deviceId;

    private static final String SUPABASE_URL = "https://owckvahinoewzundfcpv.supabase.co";
    private static final String SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93Y2t2YWhpbm9ld3p1bmRmY3B2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE2ODAzOTQsImV4cCI6MjA5NzI1NjM5NH0.mNSeY8dpZQD1aqFACY3CcZQV3SS1wOZreKi9zkLxFpg";

    public class JsBridge {
        @JavascriptInterface
        public void reportAnswer(final int questionId, final boolean isCorrect) {
            new Thread(new Runnable() {
                @Override
                public void run() {
                    try {
                        URL url = new URL(SUPABASE_URL + "/rest/v1/answer_logs");
                        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                        conn.setConnectTimeout(5000);
                        conn.setReadTimeout(5000);
                        conn.setRequestMethod("POST");
                        conn.setDoOutput(true);
                        conn.setRequestProperty("Content-Type", "application/json");
                        conn.setRequestProperty("apikey", SUPABASE_KEY);
                        conn.setRequestProperty("Authorization", "Bearer " + SUPABASE_KEY);
                        conn.setRequestProperty("Prefer", "return=minimal");
                        String body = "{\"question_id\":" + questionId + ",\"is_correct\":" + isCorrect + ",\"device_id\":\"" + deviceId + "\"}";
                        OutputStream os = conn.getOutputStream();
                        os.write(body.getBytes("UTF-8"));
                        os.close();
                        conn.getInputStream().close();
                        conn.disconnect();
                    } catch (Exception e) {
                        // silently ignore
                    }
                }
            }).start();
        }

        @JavascriptInterface
        public String getDeviceId() {
            return deviceId;
        }

        @JavascriptInterface
        public void checkForUpdateBridge() {
            new Thread(new Runnable() {
                @Override
                public void run() {
                    try {
                        URL url = new URL("https://zuixin123123123.github.io/microbio-quiz/version.json?_t=" + System.currentTimeMillis());
                        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                        conn.setConnectTimeout(5000);
                        conn.setReadTimeout(5000);
                        java.util.Scanner s = new java.util.Scanner(conn.getInputStream(), "UTF-8").useDelimiter("\\A");
                        final String json = s.hasNext() ? s.next() : "";
                        s.close();
                        conn.disconnect();
                        if (!json.isEmpty()) {
                            final String escaped = json.replace("\\", "\\\\").replace("'", "\\'");
                            webView.post(new Runnable() {
                                @Override
                                public void run() {
                                    webView.evaluateJavascript("onUpdateResult('" + escaped + "')", null);
                                }
                            });
                        }
                    } catch (Exception e) { /* no update — network may be unavailable */ }
                }
            }).start();
        }

        @JavascriptInterface
        public void ping() {
            // no-op
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            getWindow().addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
            getWindow().setStatusBarColor(Color.parseColor("#4f46e5"));
            getWindow().setNavigationBarColor(Color.parseColor("#f0f2f5"));
        }

        webView = new WebView(this);
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setDatabaseEnabled(true);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }

        settings.setAllowFileAccessFromFileURLs(true);
        settings.setAllowUniversalAccessFromFileURLs(true);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
            WebView.setWebContentsDebuggingEnabled(true);
        }

        // Generate short device ID from ANDROID_ID
        try {
            String aid = Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID);
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] hash = md.digest(aid.getBytes("UTF-8"));
            StringBuilder sb = new StringBuilder();
            for (byte b : hash) sb.append(String.format("%02x", b));
            deviceId = sb.toString().substring(0, 8);
        } catch (Exception e) {
            deviceId = "unknown";
        }

        webView.addJavascriptInterface(new JsBridge(), "MicrobioBridge");

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String url = request.getUrl().toString();
                if (url.startsWith("http://") || url.startsWith("https://")) {
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    view.getContext().startActivity(intent);
                    return true;
                }
                return false;
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if (url.startsWith("http://") || url.startsWith("https://")) {
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    view.getContext().startActivity(intent);
                    return true;
                }
                return false;
            }

            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                String url = request.getUrl().toString();
                // Proxy version.json requests to bypass CORS
                if (url.contains("version.json")) {
                    try {
                        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
                        conn.setConnectTimeout(5000);
                        conn.setReadTimeout(5000);
                        InputStream is = conn.getInputStream();
                        String ct = conn.getContentType();
                        return new WebResourceResponse(ct != null ? ct : "application/json", "UTF-8", is);
                    } catch (Exception e) {
                        return null;
                    }
                }
                return null;
            }
        });
        webView.setWebChromeClient(new WebChromeClient());

        webView.loadUrl("file:///android_asset/www/index.html");
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
