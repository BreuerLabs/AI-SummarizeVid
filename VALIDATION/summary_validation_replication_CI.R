library(xtable)

setwd("/Users/adambreuer/Downloads/political_tv_ads_project/AI-SummarizeVid/VALIDATION")



coder1<-read.csv('validation_data/summary_coder1.csv',as.is=T)
coder1$coder = 'coder1'
coder2<-read.csv('validation_data/summary_coder2.csv',as.is=T)
coder2$coder = 'coder2'
coder3<-read.csv('validation_data/summary_coder3.csv',as.is=T)
coder3$coder = 'coder3'
coder4<-read.csv('validation_data/summary_coder4.csv',as.is=T)
coder4$coder = 'coder4'

coder1 = coder1[with(coder1, order(ad, question_type)), ]
coder2 = coder2[with(coder2, order(ad, question_type)), ]
coder3 = coder3[with(coder3, order(ad, question_type)), ]
coder4 = coder4[with(coder4, order(ad, question_type)), ]


META <-read.csv('../METADATA.csv')
META$FILE_ID =gsub(META$FILENAME, pattern=".mp4", replacement="")



# Do ratings of GPT depend on election year, party, or their interaction?
allcoders = rbind(coder1, coder2, coder3, coder4)
# allcoders$GPT_rescaled = (allcoders$GPT+2)/4.0 # rescale [-2, 2] to [0,1]

allcoders$ID = gsub(" ", "-", allcoders$ad)

setdiff(allcoders$ID,META$FILE_ID)

allcoders = merge(allcoders, META[,c('FILE_ID', 'PARTY', 'ELECTION')], by.x='ID', by.y='FILE_ID')
length(unique(coder1$ad)) == length(unique(allcoders$ID)) # Assert that all id's are accounted for


# Check all datasets have the same ad and quality ID in each row before taking means
all(coder1$ad== coder2$ad) 
all(coder1$ad== coder3$ad) 
all(coder1$ad== coder4$ad) 
all(coder1$question_type == coder2$question_type) 
all(coder1$question_type == coder3$question_type) 
all(coder1$question_type == coder4$question_type) 

rowmeans_human_df <- aggregate(allcoders$human, by=list(allcoders$ad, allcoders$question_type), FUN=function(x){mean(x, na.rm = TRUE)})
rowmeans_GPT_df <- aggregate(allcoders$GPT, by=list(allcoders$ad, allcoders$question_type), FUN=function(x){mean(x, na.rm = TRUE)})
colnames(rowmeans_human_df) <- colnames(rowmeans_GPT_df) <- c('ad', 'question_type', 'meanrating')



###          Create our t-test table            ###
### ### ### ### ### ### ### ### ### ### ### ### ###
row1_test<-t.test(rowmeans_human_df[rowmeans_human_df$question_type=='coherent', 'meanrating'], rowmeans_GPT_df[rowmeans_GPT_df $question_type=='coherent', 'meanrating'],var.equal=T)
	  			  
row1<-c('Coherence','Coherent and easy to understand', 
	round(as.numeric(row1_test$estimate[2]),2),round(as.numeric(row1_test$estimate[1]),2), 
	round(as.numeric(row1_test$estimate[2])  - as.numeric(row1_test$estimate[1]),2), round(row1_test$conf.int[1], 3), round(row1_test$conf.int[2],3),
	round(abs(as.numeric(row1_test$statistic)),3),round(abs(as.numeric(row1_test$p.value)),3))

row2_test<-t.test(rowmeans_human_df[rowmeans_human_df $question_type=='factual','meanrating'], rowmeans_GPT_df[rowmeans_GPT_df $question_type=='factual', 'meanrating'],var.equal=T)	 
row2<-c('Consistency','Factually consistent with the advertisement',round(as.numeric(row2_test$estimate[2]),2),round(as.numeric(row2_test$estimate[1]),2),
	round(as.numeric(row2_test$estimate[2])  - as.numeric(row2_test$estimate[1]),2), round(row2_test$conf.int[1], 3), round(row2_test$conf.int[2],3),
	round(abs(as.numeric(row2_test$statistic)),3),round(abs(as.numeric(row2_test$p.value)),3))

row3_test<-t.test(rowmeans_human_df[rowmeans_human_df $question_type=='themes', 'meanrating'], rowmeans_GPT_df[rowmeans_GPT_df $question_type=='themes', 'meanrating'],var.equal=T)	 
row3<-c('Fluency','Contains the main themes of the advertisement',round(as.numeric(row3_test$estimate[2]),2),round(as.numeric(row3_test$estimate[1]),2),
	round(as.numeric(row3_test$estimate[2])  - as.numeric(row3_test$estimate[1]),2), round(row3_test$conf.int[1], 3), round(row3_test$conf.int[2],3),
	round(abs(as.numeric(row3_test$statistic)),4),round(abs(as.numeric(row3_test$p.value)),3))

row4_test<-t.test(rowmeans_human_df[rowmeans_human_df $question_type=='useful', 'meanrating'], rowmeans_GPT_df[rowmeans_GPT_df $question_type=='useful', 'meanrating'],var.equal=T)	 
row4<-c('Relevancy','Useful for research on presidential advertisements',round(as.numeric(row4_test$estimate[2]),2),round(as.numeric(row4_test$estimate[1]),2),
	round(as.numeric(row4_test$estimate[2])  - as.numeric(row4_test$estimate[1]),2), round(row4_test$conf.int[1], 3), round(row4_test$conf.int[2],3),
	round(abs(as.numeric(row4_test$statistic)),3),round(abs(as.numeric(row4_test$p.value)),3))

rowmeans_human_df_comb4 = aggregate(rowmeans_human_df$meanrating, list(coder1$ad), mean)
rowmeans_GPT_df_comb4 = aggregate(rowmeans_GPT_df$meanrating, list(coder1$ad), mean)
all(rowmeans_human_df_comb4$Group.1 == rowmeans_GPT_df_comb4$Group.1) # same ordering of ads so OK to pair

row5_test<-t.test(rowmeans_human_df_comb4$x, rowmeans_GPT_df_comb4$x, var.equal=T)
row5<-c('Overall','',round(as.numeric(row5_test$estimate[2]),2),round(as.numeric(row5_test$estimate[1]),2),
	round(as.numeric(row5_test$estimate[2])  - as.numeric(row5_test$estimate[1]),2), round(row5_test$conf.int[1], 3), round(row5_test$conf.int[2],3),
round(abs(as.numeric(row5_test$statistic)),3),round(abs(as.numeric(row5_test$p.value)),3))

results<-rbind(row1,row2,row3,row4,row5)
colnames(results)<-c('Dimension','Definition','LLM Summary','Human Summary','t-statistic','p-value')
results
# print(xtable(results),type='html',file='table_4_final.html',include.rownames =FALSE)
xtable(results)



## Alternative: Paired samples Wilcoxon test
###          Create our t-test table            ###
### ### ### ### ### ### ### ### ### ### ### ### ###
Wrow1_test<-wilcox.test(rowmeans_human_df[rowmeans_human_df $question_type=='coherent', 'meanrating'], rowmeans_GPT_df[rowmeans_GPT_df $question_type=='coherent', 'meanrating'], paired=T, conf.int = T)               
Wrow1<-c('Coherence','Coherent and easy to understand',  round(Wrow1_test $conf.int[1], 5), round(Wrow1_test $conf.int[2], 5),
    round(abs(as.numeric(Wrow1_test$statistic)),3),round(abs(as.numeric(Wrow1_test$p.value)),3))

Wrow2_test<-wilcox.test(rowmeans_human_df[rowmeans_human_df $question_type=='factual', 'meanrating'], rowmeans_GPT_df[rowmeans_GPT_df $question_type=='factual', 'meanrating'], paired=T, conf.int = T)    
Wrow2<-c('Consistency','Factually consistent with the advertisement',  round(Wrow2_test $conf.int[1], 5), round(Wrow2_test $conf.int[2], 5),
round(abs(as.numeric(Wrow2_test$statistic)),3),round(abs(as.numeric(Wrow2_test$p.value)),3))

Wrow3_test<-wilcox.test(rowmeans_human_df[rowmeans_human_df $question_type=='themes', 'meanrating'], rowmeans_GPT_df[rowmeans_GPT_df $question_type=='themes', 'meanrating'], paired=T, conf.int = T)  
Wrow3<-c('Fluency','Contains the main themes of the advertisement',  round(Wrow3_test $conf.int[1], 5), round(Wrow3_test $conf.int[2], 5),
round(abs(as.numeric(Wrow3_test$statistic)),3),round(abs(as.numeric(Wrow3_test$p.value)),3))

Wrow4_test<-wilcox.test(rowmeans_human_df[rowmeans_human_df $question_type=='useful', 'meanrating'], rowmeans_GPT_df[rowmeans_GPT_df $question_type=='useful', 'meanrating'], paired=T, conf.int = T)  
Wrow4<-c('Relevancy','Useful for research on presidential advertisements',  round(Wrow4_test $conf.int[1], 5), round(Wrow4_test $conf.int[2], 5),
round(abs(as.numeric(Wrow4_test$statistic)),3),round(abs(as.numeric(Wrow4_test$p.value)),3))

Wrow5_test<-wilcox.test(rowmeans_human_df_comb4$x, rowmeans_GPT_df_comb4$x,  paired=T, conf.int = T)
Wrow5<-c('Overall','', round(Wrow5_test $conf.int[1], 5), round(Wrow5_test $conf.int[2], 5),
round(abs(as.numeric(Wrow5_test$statistic)),3),round(abs(as.numeric(Wrow5_test$p.value)),3))

wresults<-rbind(Wrow1,Wrow2,Wrow3,Wrow4,Wrow5)
colnames(wresults)<-c('Dimension','Definition','CI_left', 'CI_right', 'V','p-value')
wresults
# print(xtable(wresults),type='html',file='table_5_final.html',include.rownames =FALSE)
xtable(wresults[,c('CI_left', 'CI_right')])


# Melt the data to regress the scores
library(reshape2)
allcoders_long <- melt(allcoders[,c('ID', 'question_type', 'coder', 'human', 'PARTY', 'ELECTION', 'GPT')], id = c('ID', 'question_type', 'coder', 'PARTY', 'ELECTION'))
allcoders_long = na.omit(allcoders_long)
# Convert Likert ratings to an ordered factor 
colnames(allcoders_long)[colnames(allcoders_long) == "value"] <- "rating"
colnames(allcoders_long)[colnames(allcoders_long) == "variable"] <- "human_or_AI"
allcoders_long $rating_factor <- factor(allcoders_long$rating, ordered = TRUE)
allcoders_long$AI =  as.numeric(allcoders_long$human_or_AI=='GPT')
allcoders$AIgreater = allcoders$GPT > allcoders$human



library(ordinal)
library(sandwich)
library(clubSandwich) 
library(lmtest)

allcoders_long$ELECTION_demeaned = (allcoders_long$ELECTION - mean(allcoders_long$ELECTION))/sd(allcoders_long$ELECTION)
allcoders_long$republican = allcoders_long$PARTY=='Republican'
print("NOTE: election")


## Cumulative Link Mixed Model fitted with the Laplace approximation
coh_paired_ordinal_model <- clmm(rating_factor ~ human_or_AI + republican + ELECTION_demeaned + ELECTION_demeaned*republican + (1 | coder) +  (1 | ID) , data=allcoders_long[allcoders_long$question_type=='coherent',])
summary(coh_paired_ordinal_model)

fact_paired_ordinal_model <- clmm(rating_factor ~ human_or_AI + republican + ELECTION_demeaned + ELECTION_demeaned*republican + (1 | coder) +  (1 | ID) , data=allcoders_long[allcoders_long$question_type=='factual',])
summary(fact_paired_ordinal_model)

theme_paired_ordinal_model <- clmm(rating_factor ~ human_or_AI + republican + ELECTION_demeaned + ELECTION_demeaned*republican + (1 | coder) +  (1 | ID) , data=allcoders_long[allcoders_long$question_type=='themes',])
summary(theme_paired_ordinal_model)

use_paired_ordinal_model <- clmm(rating_factor ~ human_or_AI + republican + ELECTION_demeaned + ELECTION_demeaned*republican + (1 | coder) +  (1 | ID) , data=allcoders_long[allcoders_long$question_type=='useful',])
summary(use_paired_ordinal_model)


boot_clmm_clustered <- function(data, indices) {
  # Resample movie IDs first (clustered resampling)
  sampled_IDs <- unique(data$ID)[indices]  
  data_boot <- data[data$ID %in% sampled_IDs, ]

  # Fit the model
  model <- clmm(rating_factor ~ human_or_AI + republican + 
                    ELECTION_demeaned + ELECTION_demeaned*republican + 
                    (1 | coder) + (1 | ID), 
                    data = data_boot)
  coefs <- coef(summary(model))[,1]  

  coef_all <- rep(0, length(coef_orig_names))
  names(coef_all) <- coef_orig_names
  for (idx in 1:length(coefs)){
    coef_all[names(coef_all)==names(coefs[idx])] <- coefs[idx]
  }
  return(coef_all)  # Extract fixed-effect coefficients
}



set.seed(50003)

# Bootstrap 
library(boot)
coef_orig_names = c("-2|-1","-1|0","0|1" , "1|2","human_or_AIGPT" ,"republicanTRUE","ELECTION_demeaned", "republicanTRUE:ELECTION_demeaned")
boot_results_coherent <- boot(data = allcoders_long[allcoders_long$question_type == 'coherent',], 
                     # statistic = boot_clmm, 
                     statistic = boot_clmm_clustered, 
                     R = 5000, parallel = "multicore", ncpus = 12) 
results_coherent <- data.frame(
  Estimate = coef(summary(coh_paired_ordinal_model))[,1],
  Boot_SE = apply(boot_results_coherent $t, 2, sd)
)
results_coherent$t_values_boot =  results_coherent$Estimate / results_coherent$Boot_SE
results_coherent$p_values_boot <- 2 * (1 - pnorm(abs(results_coherent$t_values_boot)))
results_coherent

boot_results_factual <- boot(data = allcoders_long[allcoders_long$question_type == 'factual',], 
                     #statistic = boot_clmm, 
                     statistic = boot_clmm_clustered, 
                     R = 5000, parallel = "multicore", ncpus = 12) 
results_factual <- data.frame(
  Estimate = coef(summary(fact_paired_ordinal_model))[,1],
  Boot_SE = apply(boot_results_factual $t, 2, sd)
)
results_factual$t_values_boot =  results_factual$Estimate / results_factual$Boot_SE
results_factual$p_values_boot <- 2 * (1 - pnorm(abs(results_factual$t_values_boot)))
results_factual

boot_results_themes <- boot(data = allcoders_long[allcoders_long$question_type == 'themes',], 
                     #statistic = boot_clmm, 
                     statistic = boot_clmm_clustered, 
                     R = 5000, parallel = "multicore", ncpus = 12) 
results_themes <- data.frame(
  Estimate = coef(summary(theme_paired_ordinal_model))[,1],
  Boot_SE = apply(boot_results_themes $t, 2, sd)
)
results_themes$t_values_boot =  results_themes$Estimate / results_themes$Boot_SE
results_themes$p_values_boot <- 2 * (1 - pnorm(abs(results_themes$t_values_boot)))
results_themes

boot_results_useful <- boot(data = allcoders_long[allcoders_long$question_type == 'useful',], 
                     #statistic = boot_clmm, 
                     statistic = boot_clmm_clustered, 
                     R = 5000, parallel = "multicore", ncpus = 12) 
results_useful <- data.frame(
  Estimate = coef(summary(use_paired_ordinal_model))[,1],
  Boot_SE = apply(boot_results_useful $t, 2, sd)
)
results_useful$t_values_boot =  results_useful$Estimate / results_useful$Boot_SE
results_useful$p_values_boot <- 2 * (1 - pnorm(abs(results_useful$t_values_boot)))
results_useful



print("NOTE: MEOL computed with standardized (demeaned and rescaled) election year. OLS doesnt need to do that for stability. MUST CONVERT MEOL ESTIMATES and std errors back before comparing to OLS!" )


## Sanity check: standard linear regression (even though the assumptions don't match particularly well here)
# CR1 = cluster robust standard errors here
all_coders_long_coherent <-  allcoders_long[allcoders_long$question_type=='coherent',]
coherent_sanity_check_linearmodel <- lm(data= all_coders_long_coherent, rating ~ AI + PARTY + ELECTION + PARTY*ELECTION)
summary(coherent_sanity_check_linearmodel)
robust_se_multi_coh <- vcovCR(coherent_sanity_check_linearmodel, cluster = all_coders_long_coherent$ID, type = "CR1") 
robust_coh <- coeftest(coherent_sanity_check_linearmodel, vcov. = robust_se_multi_coh)
robust_SE_coh <- robust_coh[,2]; rownames(robust_SE_coh) <- names(robust_coh)
robust_coh

all_coders_long_factual <-  allcoders_long[allcoders_long$question_type=='factual',]
fact_sanity_check_linearmodel <- lm(data= all_coders_long_factual, rating ~ AI + PARTY + ELECTION + PARTY*ELECTION)
summary(fact_sanity_check_linearmodel)
robust_se_multi_fact <- vcovCR(fact_sanity_check_linearmodel, cluster = all_coders_long_factual$ID, type = "CR1") 
robust_fact <- coeftest(fact_sanity_check_linearmodel, vcov. = robust_se_multi_fact)
robust_SE_fact <- robust_fact[,2]; rownames(robust_SE_fact) <- names(robust_fact)
robust_fact

all_coders_long_themes <-  allcoders_long[allcoders_long$question_type=='themes',]
theme_sanity_check_linearmodel <- lm(data= all_coders_long_themes, rating ~ AI + PARTY + ELECTION + PARTY*ELECTION)
summary(theme_sanity_check_linearmodel)
robust_se_multi_theme <- vcovCR(theme_sanity_check_linearmodel, cluster = all_coders_long_themes$ID, type = "CR1") 
robust_themes <- coeftest(theme_sanity_check_linearmodel, vcov. = robust_se_multi_theme)
robust_SE_themes <- robust_themes[,2]; rownames(robust_SE_themes) <- names(robust_themes)
robust_themes

all_coders_long_useful <-  allcoders_long[allcoders_long$question_type=='useful',]
useful_sanity_check_linearmodel <- lm(data= all_coders_long_useful, rating ~ AI + PARTY + ELECTION + PARTY*ELECTION)
summary(useful_sanity_check_linearmodel)
robust_se_multi_use <- vcovCR(useful_sanity_check_linearmodel, cluster = all_coders_long_useful$ID, type = "CR1") 
robust_use <- coeftest(useful_sanity_check_linearmodel, vcov. = robust_se_multi_use)
robust_SE_use <- robust_use[,2]; rownames(robust_SE_use) <- names(robust_use)
robust_use



## OLS Linear Regression with ad fixed effects and rater-clustered FErobust standard errors:
##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### 
library(fixest) # More numerically stable estimation with many fixed effects

all_coders_long_coherent <-  allcoders_long[allcoders_long$question_type=='coherent',]
coherent_FE_linearmodel <- feols(data = all_coders_long_coherent,  rating ~ AI | ID )
summary(coherent_FE_linearmodel, se = "hetero")

all_coders_long_factual <-  allcoders_long[allcoders_long$question_type=='factual',]
fact_FE_linearmodel <- feols(data= all_coders_long_factual, rating ~ AI | ID )
summary(fact_FE_linearmodel , se = "hetero")

all_coders_long_themes <-  allcoders_long[allcoders_long$question_type=='themes',]
theme_FE_linearmodel <- feols(data= all_coders_long_themes, rating ~ AI | ID )
summary(theme_FE_linearmodel , se = "hetero")

all_coders_long_useful <-  allcoders_long[allcoders_long$question_type=='useful',]
useful_FE_linearmodel <- feols(data= all_coders_long_useful, rating ~ AI | ID )
summary(useful_FE_linearmodel, se = "hetero")



# Automatically set up the regression table
# Stargazer needs short names!
cp <- coh_paired_ordinal_model; fp<- fact_paired_ordinal_model; tp<- theme_paired_ordinal_model; up<- use_paired_ordinal_model
cl <- coherent_sanity_check_linearmodel; fl<- fact_sanity_check_linearmodel; tl<- theme_sanity_check_linearmodel; ul <-useful_sanity_check_linearmodel
# Stargazer won't read a clmm model object, so add placeholder OLS models for each CLMM to fill manually in latex
library(stargazer)
stargazer(
cl, cl, fl, fl, tl, tl, ul, ul,
se=list(robust_SE_coh, robust_SE_coh, robust_SE_fact, robust_SE_fact, robust_SE_themes, robust_SE_themes, robust_SE_use, robust_SE_use),
title="Human-to-AI Summary Comparison Results",
align=TRUE, 
dep.var.labels=c("Overall Rating","High Rating"),
covariate.labels=c("AI","Republican","ElectionYear","Repub.*Elec.Year"),
omit.stat=c("LL","ser","f")
)



