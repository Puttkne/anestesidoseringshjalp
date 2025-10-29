import streamlit as st
import pandas as pd
import database as db
import auth
from config import APP_CONFIG

def render_learning_tab(procedures_df):
    st.header("🧠 Inlärning & Modeller")
    st.markdown("""
    Appen använder två inlärningssystem parallellt för att bli smartare över tid. Båda systemen blir mer stabila och "trögare" ju mer data de får, vilket skyddar mot att enskilda avvikande fall skapar opålitliga rekommendationer.
    - **Regelmotorn** justerar sin dos baserat på ett "fingeravtryck" av fallet. Inlärningen är dämpad, vilket innebär att extrema VAS-värden har en minskad proportionerlig påverkan.
    - **XGBoost-modellen** är en avancerad ML-modell som tränas om på all insamlad data för ett specifikt ingrepp. Den lär sig komplexa mönster och blir mer robust ju större datamängden är.
    """)
    learn_tabs = st.tabs(["Modellstatus per Ingrepp", "Regelmotor-inlärning", "Statistik"])

    with learn_tabs[0]:
        st.subheader("ML-Modellens Aktiveringsstatus")
        st.markdown(f"XGBoost-modellen aktiveras för ett specifikt ingrepp när **{APP_CONFIG['ML_THRESHOLD_PER_PROCEDURE']}** fall har loggats för det.")

        all_cases = db.get_all_cases()
        cases_df_stat = pd.DataFrame(all_cases) if all_cases else pd.DataFrame()

        if not cases_df_stat.empty and 'procedure_id' in cases_df_stat.columns:
            case_counts = cases_df_stat['procedure_id'].value_counts().reset_index()
            case_counts.columns = ['id', 'Antal Fall']

            status_df = procedures_df.merge(case_counts, on='id', how='left').fillna(0)
            status_df['Antal Fall'] = status_df['Antal Fall'].astype(int)
            status_df['Modellstatus'] = status_df['Antal Fall'].apply(lambda x: '✅ Aktiv' if x >= APP_CONFIG['ML_THRESHOLD_PER_PROCEDURE'] else '⏳ Inaktiv')
            status_df.rename(columns={'name': 'Ingrepp', 'specialty': 'Specialitet'}, inplace=True)

            st.dataframe(status_df[['Specialitet', 'Ingrepp', 'Antal Fall', 'Modellstatus']], use_container_width=True)
        else:
            st.info("Inga fall har loggats ännu för att kunna avgöra modellstatus.")

    with learn_tabs[1]:
        st.subheader("Regelmotorns Personliga Kalibreringsprofil")

        st.markdown("### 💊 Adjuvanteffektivitet per Smärttyp")
        st.markdown("Varje adjuvant har olika effektivitet (0-10) för de tre smärttyperna:")
        st.caption("🔴 **Somatisk** | 🔵 **Visceral** | 🟢 **Neuropatisk**")

        # Skapa en tabell med alla adjuvanter och deras effektivitet per smärttyp
        adjuvant_data = {
            "Adjuvant": [
                "Paracetamol 1g",
                "NSAID (Ibuprofen 400mg)",
                "Ketorolac 30mg",
                "Parecoxib 40mg",
                "Catapressan (Klonidin)",
                "Droperidol",
                "Ketamin liten bolus",
                "Ketamin stor bolus",
                "Ketamin liten infusion",
                "Ketamin stor infusion",
                "Lidokain Bolus",
                "Lidokain Infusion",
                "Betapred 4 mg",
                "Betapred 8 mg",
                "Sevofluran",
                "Infiltration"
            ],
            "Dos-reduktion": [
                "-15%",
                "-20%",
                "-25%",
                "-20%",
                "-20%",
                "-15%",
                "-10%",
                "-20%",
                "-15%",
                "-30%",
                "-10%",
                "-20%",
                "-10%",
                "-15%",
                "-10%",
                "-15%"
            ],
            "🔴 Somatisk": [7, 9, 9, 8, 2, 5, 5, 6, 5, 6, 3, 4, 3, 4, 6, 8],
            "🔵 Visceral": [5, 3, 2, 3, 8, 5, 6, 7, 6, 7, 7, 8, 7, 8, 5, 4],
            "🟢 Neuropatisk": [3, 1, 1, 1, 6, 5, 7, 8, 7, 8, 5, 6, 2, 3, 4, 2]
        }

        adj_df = pd.DataFrame(adjuvant_data)

        st.dataframe(
            adj_df,
            column_config={
                "Adjuvant": st.column_config.TextColumn("Adjuvant", width="medium"),
                "Dos-reduktion": st.column_config.TextColumn("Dos-reduktion", width="small"),
                "🔴 Somatisk": st.column_config.ProgressColumn(
                    "🔴 Somatisk",
                    help="Effektivitet mot somatisk smärta (0-10)",
                    format="%d/10",
                    min_value=0,
                    max_value=10,
                    width="small"
                ),
                "🔵 Visceral": st.column_config.ProgressColumn(
                    "🔵 Visceral",
                    help="Effektivitet mot visceral smärta (0-10)",
                    format="%d/10",
                    min_value=0,
                    max_value=10,
                    width="small"
                ),
                "🟢 Neuropatisk": st.column_config.ProgressColumn(
                    "🟢 Neuropatisk",
                    help="Effektivitet mot neuropatisk smärta (0-10)",
                    format="%d/10",
                    min_value=0,
                    max_value=10,
                    width="small"
                ),
            },
            hide_index=True,
            use_container_width=True
        )

        st.caption("💡 **Tips:** Dessa värden kombineras med ingreppets smärtprofil för optimal dosering. Systemet lär sig över tid och justerar effektiviteten baserat på faktiska utfall.")

        st.divider()

        st.markdown("### 🧠 Inlärda Justeringsfaktorer")
        user_id = auth.get_current_user_id()
        factors = db.get_all_calibration_factors(user_id)

        if not factors:
            st.info("Ingen specifik inlärning för regelmotorn har skett ännu. När du sparar fall kommer systemet att lära sig och justera doserna automatiskt.")
        else:
            sorted_factors = sorted(factors.items(), key=lambda item: abs(item[1] - 1), reverse=True)
            factor_data = {"Fingeravtryck": [k for k, v in sorted_factors], "Justeringsfaktor": [v for k, v in sorted_factors]}
            df = pd.DataFrame(factor_data)
            st.dataframe(df, column_config={
                "Justeringsfaktor": st.column_config.ProgressColumn("Faktor", format="x%.3f", min_value=0.2, max_value=3.0)
            }, use_container_width=True)
            st.caption(f"📊 Totalt {len(factors)} unika konfigurationer har tränats baserat på dina fall.")

    with learn_tabs[2]:
        st.subheader("📊 Statistik & Analys")

        all_cases = db.get_all_cases()
        cases_df_analysis = pd.DataFrame(all_cases) if all_cases else pd.DataFrame()

        if cases_df_analysis.empty:
            st.info("Inga fall har loggats ännu för att visa statistik.")
        else:
            cases_df_analysis['procedure_name'] = cases_df_analysis['procedure_id'].apply(
                lambda x: procedures_df.loc[procedures_df['id'] == x, 'name'].iloc[0] if x and x in procedures_df['id'].values else 'Okänt'
            )

            st.markdown("### Övergripande statistik")
            stat_cols = st.columns(4)
            with stat_cols[0]:
                st.metric("Totalt antal fall", len(cases_df_analysis))
            with stat_cols[1]:
                avg_vas = cases_df_analysis['vas'].mean()
                st.metric("Genomsnittligt VAS", f"{avg_vas:.1f}")
            with stat_cols[2]:
                high_vas_pct = (cases_df_analysis['vas'] > 4).sum() / len(cases_df_analysis) * 100
                st.metric("Andel VAS >4", f"{high_vas_pct:.1f}%")
            with stat_cols[3]:
                avg_dose = cases_df_analysis['givenDose'].mean()
                st.metric("Genomsnittlig dos", f"{avg_dose:.1f} mg")

            st.divider()

            st.markdown("### Statistik per ingrepp")
            proc_stats = cases_df_analysis.groupby('procedure_name').agg({
                'vas': ['mean', 'max', lambda x: (x > 4).sum()],
                'givenDose': ['mean', 'min', 'max'],
                'procedure_id': 'count'
            }).round(1)
            proc_stats.columns = ['Medel VAS', 'Max VAS', 'Antal VAS >4', 'Medel Dos (mg)', 'Min Dos', 'Max Dos', 'Antal Fall']
            proc_stats = proc_stats.sort_values('Antal Fall', ascending=False)
            st.dataframe(proc_stats, use_container_width=True)

            st.divider()

            st.markdown("### VAS-fördelning")
            vas_counts = cases_df_analysis['vas'].value_counts().sort_index()
            st.bar_chart(vas_counts)

            st.divider()

            st.markdown("### Trend: Senaste 30 fallen")
            if len(cases_df_analysis) >= 5:
                recent_cases = cases_df_analysis.sort_values('timestamp', ascending=False).head(30)
                trend_cols = st.columns(2)

                with trend_cols[0]:
                    st.write("**VAS över tid**")
                    vas_trend = recent_cases.sort_values('timestamp')[['timestamp', 'vas']].reset_index(drop=True)
                    st.line_chart(vas_trend.set_index('timestamp')['vas'])

                with trend_cols[1]:
                    st.write("**Given dos över tid**")
                    dose_trend = recent_cases.sort_values('timestamp')[['timestamp', 'givenDose']].reset_index(drop=True)
                    st.line_chart(dose_trend.set_index('timestamp')['givenDose'])

            st.divider()

            st.markdown("### Aktivitet per användare")
            if 'user_id' in cases_df_analysis.columns:
                cases_df_analysis['created_by_name'] = cases_df_analysis['user_id'].apply(
                    lambda x: db.get_user_by_id(x)['username'] if db.get_user_by_id(x) else 'Okänd'
                )
                user_stats = cases_df_analysis.groupby('created_by_name').agg({
                    'procedure_id': 'count',
                    'vas': 'mean',
                    'givenDose': 'mean'
                }).round(1)
                user_stats.columns = ['Antal Fall', 'Medel VAS', 'Medel Dos (mg)']
                user_stats = user_stats.sort_values('Antal Fall', ascending=False)
                st.dataframe(user_stats, use_container_width=True)
