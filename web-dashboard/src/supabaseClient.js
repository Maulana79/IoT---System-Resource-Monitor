import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://btipbbeujlpulcjcvhoz.supabase.co'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ0aXBiYmV1amxwdWxjamN2aG96Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2MDg2ODQsImV4cCI6MjA5MzE4NDY4NH0.2DBe7rBoTaw-fRSXyjqOwgxoWttsfLgwVuxPVtk5zao'

export const supabase = createClient(supabaseUrl, supabaseKey)