package id.ac.umkt.ppb.thermalmonitor

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

class MainActivity : AppCompatActivity() {

    // --- KONFIGURASI SUPABASE ---
    private val supabaseUrl = "https://btipbbeujlpulcjcvhoz.supabase.co/rest/v1/temperature_logs"
    private val supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ0aXBiYmV1amxwdWxjamN2aG96Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2MDg2ODQsImV4cCI6MjA5MzE4NDY4NH0.2DBe7rBoTaw-fRSXyjqOwgxoWttsfLgwVuxPVtk5zao"

    // Mengambil nama tipe HP secara otomatis (misal: "SM-A515F" atau "POCO X3")
    private val deviceName = "HP - ${Build.MODEL}"

    private val client = OkHttpClient()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Bikin UI teks sederhana di tengah layar pakai kode (tanpa perlu edit XML)
        val textView = TextView(this).apply {
            text = "Monitoring Suhu Aktif untuk $deviceName...\nBiarkan aplikasi ini terbuka."
            textSize = 18f
            setPadding(32, 32, 32, 32)
        }
        setContentView(textView)

        // Jalankan proses monitoring di background (Coroutine)
        startMonitoring()
    }

    private fun startMonitoring() {
        lifecycleScope.launch(Dispatchers.IO) {
            while (true) {
                val currentTemp = getBatteryTemperature()

                if (currentTemp > 0) {
                    sendToSupabase(currentTemp)
                }

                // Jeda 60 detik (60000 milidetik) sebelum mengirim data lagi
                delay(60000)
            }
        }
    }

    private fun getBatteryTemperature(): Float {
        val intentFilter = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        val batteryStatus = this.registerReceiver(null, intentFilter)

        // Sensor Android mengembalikan suhu dalam satuan persepuluh derajat Celcius
        // Jadi angka 350 artinya 35.0°C
        val tempInt = batteryStatus?.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0) ?: 0
        return tempInt / 10.0f
    }

    private fun getRamUsage(): Float {
        val activityManager = getSystemService(Context.ACTIVITY_SERVICE) as android.app.ActivityManager
        val memoryInfo = android.app.ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memoryInfo)

        val usedMem = memoryInfo.totalMem - memoryInfo.availMem
        return ((usedMem.toDouble() / memoryInfo.totalMem.toDouble()) * 100).toFloat()
    }
    private fun sendToSupabase(temperature: Float) {
        try {
            // Siapkan data JSON
            val jsonObject = JSONObject().apply {
                put("device_name", deviceName)
                put("temperature", temperature)
                put("api_key", "RHS-2026-XyZ")
                put("cpu_usage", 0.0) // Kirim 0 untuk HP karena dibatasi OS
                put("ram_usage", getRamUsage())
            }

            val requestBody = jsonObject.toString().toRequestBody("application/json".toMediaType())

            // Siapkan request dengan headers Supabase API
            val request = Request.Builder()
                .url(supabaseUrl)
                .post(requestBody)
                .addHeader("apikey", supabaseKey)
                .addHeader("Authorization", "Bearer $supabaseKey")
                .addHeader("Content-Type", "application/json")
                .addHeader("Prefer", "return=minimal")
                .build()

            // Eksekusi pengiriman
            client.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    Log.d("ThermalMonitor", "Berhasil kirim suhu: $temperature°C")
                } else {
                    Log.e("ThermalMonitor", "Gagal kirim: ${response.code}")
                }
            }
        } catch (e: Exception) {
            Log.e("ThermalMonitor", "Error jaringan: ${e.message}")
        }
    }
}