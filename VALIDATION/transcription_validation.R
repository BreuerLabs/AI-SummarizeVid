library(betareg)


setwd("/Users/adambreuer/Downloads/political_tv_ads_project/AI-SummarizeVid/VALIDATION/validation_data/")


wer = read.csv('word_error_rates.csv')
META <-read.csv('../../METADATA.csv')
wer = merge(wer, META[,c('ID', 'PARTY', 'ELECTION')], by.x="COMPONENT_ID", by.y="ID")


wer$hits_over_hitssubsdels = wer$nhits / (wer$nhits+wer$nsubs+wer$ndels)
# Beta doesn't account for values of exactly 1.0 so use a standard transformation [0,1] -> (0,1)
wer$hits_over_hitssubsdels_transformed01 = (wer$hits_over_hitssubsdels * (nrow(wer)-1) + 0.5) / nrow(wer) # force between 0 and 1 #USE SQUEEZE INSTEAD

wer = wer[wer$COMPONENT_ID!='P-2114-141382',] # drop row with no words in video (0/0)

# logit_mer_hitssubsdels <- glm(data= wer, hits_over_hitssubsdels_transformed01 ~ PARTY + ELECTION + PARTY*ELECTION, family = quasibinomial) # Use MER because it is a fraction of successes so bounded 0 to 1 (and the fact that it measures successes fits nicely into the binomial -> logit framework)
# summary(logit_mer_hitssubsdels)

beta_mer_hitssubsdels <- betareg(data= wer, hits_over_hitssubsdels_transformed01 ~ PARTY + ELECTION + PARTY*ELECTION)
summary(beta_mer_hitssubsdels)


# Automatically set up the regression table
library(stargazer)
stargazer(
beta_mer_hitssubsdels,
title="Beta regression of Word Error Rate (WER) on partisanship and year",
dep.var.labels=c("Transcription Error Fraction $R_j$"),
covariate.labels=c("Republican","Election Year","Repub.*Elec.Year"),
omit.stat=c("LL","ser","f")
)