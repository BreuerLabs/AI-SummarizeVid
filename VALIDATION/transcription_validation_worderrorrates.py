import pandas as pd
import jiwer
import numpy as np
import re
import num2words # Digits => words to match
from typing import Dict, List, Tuple, Union
from jiwer.process import CharacterOutput, WordOutput, AlignmentChunk




# We modify JIWER's word alignment visualizers to make it simpler to visually compare 
# human/AI transcripts (the examples in the paper)

def visualize_alignment(
    output: Union[WordOutput, CharacterOutput],
    show_measures: bool = True,
    skip_correct: bool = True,
) -> str:
    """
    Visualize the output of [jiwer.process_words][process.process_words] and
    [jiwer.process_characters][process.process_characters]. The visualization
    shows the alignment between each processed reference and hypothesis pair.
    If `show_measures=True`, the output string will also contain all measures in the
    output.
    """
    references = output.references
    hypothesis = output.hypotheses
    alignment = output.alignments
    is_cer = isinstance(output, CharacterOutput)

    final_str = ""
    for idx, (gt, hp, chunks) in enumerate(zip(references, hypothesis, alignment)):
        if skip_correct and len(chunks) == 1 and chunks[0].type == "equal":
            continue

        final_str += f"sentence {idx+1}\n"
        final_str += _construct_comparison_string(
            gt, hp, chunks, include_space_seperator=not is_cer
        )
        final_str += "\n"

    if show_measures:
        final_str += f"number of sentences: {len(alignment)}\n"
        final_str += f"substitutions={output.substitutions} "
        final_str += f"deletions={output.deletions} "
        final_str += f"insertions={output.insertions} "
        final_str += f"hits={output.hits}\n"

        if is_cer:
            final_str += f"\ncer={output.cer*100:.2f}%\n"
        else:
            final_str += f"\nmer={output.mer*100:.2f}%"
            final_str += f"\nwil={output.wil*100:.2f}%"
            final_str += f"\nwip={output.wip*100:.2f}%"
            final_str += f"\nwer={output.wer*100:.2f}%\n"
    else:
        # remove last newline
        final_str = final_str[:-1]

    return final_str


def _construct_comparison_string(
    reference: List[str],
    hypothesis: List[str],
    ops: List[AlignmentChunk],
    include_space_seperator: bool = False,
    PRINTOKWORDS = True
) -> str:
    ref_str = "HumanReference: "
    hyp_str = "AI--Hypothesis: "
    op_str =  "   DIFFERENCES: "

    for op in ops:
        if op.type == "equal" or op.type == "substitute":
            ref = reference[op.ref_start_idx : op.ref_end_idx]
            hyp = hypothesis[op.hyp_start_idx : op.hyp_end_idx]

            op_char = "-" if op.type == "equal" else "s"
        elif op.type == "delete":
            ref = reference[op.ref_start_idx : op.ref_end_idx]
            hyp = ["*" for _ in range(len(ref))]
            op_char = "d"
        elif op.type == "insert":
            hyp = hypothesis[op.hyp_start_idx : op.hyp_end_idx]
            ref = ["*" for _ in range(len(hyp))]
            op_char = "i"
        else:
            raise ValueError(f"unparseable op name={op.type}")


        op_chars = [op_char for _ in range(len(ref))]
        for rf, hp, c in zip(ref, hyp, op_chars):
            str_len = max(len(rf), len(hp), len(c))

            if rf == "*":
                rf = "".join(["*"] * str_len)
            elif hp == "*":
                hp = "".join(["*"] * str_len)
            c = "".join([c] * str_len)

            ref_str += f"{rf:>{str_len}}"
            hyp_str += f"{hp:>{str_len}}"

            if PRINTOKWORDS !=True:
                op_str += f"{c.upper():>{str_len}}"
            elif '-' in c:
                op_str += f"{c.upper():>{str_len}}"
            else:
                op_str += f"{rf:>{str_len}}"



            if include_space_seperator:
                ref_str += " "
                hyp_str += " "
                op_str += " "

    if include_space_seperator:
        # remove last space
        return f"{ref_str[:-1]}\n\n{hyp_str[:-1]}\n\n{op_str[:-1]}\n"
    else:
        return f"{ref_str}\n\n{hyp_str}\n\n{op_str}\n"



transforms = jiwer.Compose(
    [
        jiwer.ExpandCommonEnglishContractions(),
        jiwer.RemoveEmptyStrings(),
        jiwer.ToLowerCase(),
        jiwer.RemoveMultipleSpaces(),
        jiwer.Strip(),
        # jiwer.ReduceToSingleSentence(),
        jiwer.RemovePunctuation(),
        jiwer.ReduceToListOfListOfWords(),
    ]
)
remove_trailing_thankyou_from_aitrans = True
__all__ = ["visualize_alignment"]

if __name__ == '__main__':
    

    transcript_df = pd.read_csv("validation_data/transcript_validation_data_humanverified.csv", encoding='utf8')
    COMP_ID = transcript_df['COMPONENT_ID'].values
    human_transcripts = transcript_df['TRANSCRIPTION_1_spell_checked_humverified'].values
    whisper_transcripts = transcript_df['whisper_largev3'].values

    WER_list = []
    MER_list = []

    nhits_list = []
    nsubstitutions_list = []
    ndeletions_list = []
    ninsertions_list = []

    human_trans_wordcount_list = []

    human_transcripts_alltogether = ''
    whisper_transcripts_alltogether = ''

    for idx in range(len(whisper_transcripts)):

        human_transcript = human_transcripts[idx]
        whisper_transcript = whisper_transcripts[idx]

        if remove_trailing_thankyou_from_aitrans:
            whisper_transcript = re.sub(' Thank you.', '', whisper_transcript)

        # 1 => one; 2 => two, etc.
        human_transcript = re.sub(r"(\d+)", lambda x: num2words.num2words(int(x.group(0))), human_transcript)
        whisper_transcript = re.sub(r"(\d+)", lambda x: num2words.num2words(int(x.group(0))), whisper_transcript)
        human_transcripts_alltogether = human_transcripts_alltogether + ' ' + human_transcript
        whisper_transcripts_alltogether = whisper_transcripts_alltogether + ' ' + whisper_transcript

        WER = jiwer.wer(
                    human_transcript,
                    whisper_transcript,
                    truth_transform=transforms,
                    hypothesis_transform=transforms,
                )
        MER = jiwer.mer(
                    human_transcript,
                    whisper_transcript,
                    truth_transform=transforms,
                    hypothesis_transform=transforms,
                )
        WER_list.append(WER)
        MER_list.append(MER)



        compare = jiwer.process_words(
                    human_transcript,
                    whisper_transcript,
                    reference_transform=transforms,
                    hypothesis_transform=transforms,
                )

        references=compare.references,
        hypotheses=compare.hypotheses,
        alignments=compare.alignments,
        cer=compare.wer,
        hits=compare.hits,
        substitutions=compare.substitutions,
        insertions=compare.insertions,
        deletions=compare.deletions

        nhits_list.append(hits[0])
        nsubstitutions_list.append(substitutions[0])
        ninsertions_list.append(insertions[0])
        ndeletions_list.append(deletions)


        human_trans_wordcount_list.append( len(human_transcript.split()) )

        print('\n\n')
        print('Ad ID:', COMP_ID[idx])
        print('\n')
        print(visualize_alignment(compare, skip_correct=False))

    print(WER_list)
    print('\n\n WER mean', np.mean(WER_list))
    print('\n\n MER mean', np.mean(MER_list))


    WER_overall = jiwer.wer(
                    human_transcripts_alltogether,
                    whisper_transcripts_alltogether,
                    truth_transform=transforms,
                    hypothesis_transform=transforms
                )
    MER_overall = jiwer.mer(
                    human_transcripts_alltogether,
                    whisper_transcripts_alltogether,
                    truth_transform=transforms,
                    hypothesis_transform=transforms
                )



    print('\n\n WER overall', np.mean(WER_overall))
    print('\n\n MER overall', np.mean(MER_overall), '\n\n')



    # Output ID, WER, MER dataframe for further analysis
    id_wer_output_df = pd.DataFrame({'COMPONENT_ID':COMP_ID, 'WER':WER_list, 'MER':MER_list, 'nhits':nhits_list, 
                                        'nsubs': nsubstitutions_list, 'ndels':ndeletions_list, 
                                        'ninserts':ninsertions_list, 'human_trans_wordcount':human_trans_wordcount_list})

    id_wer_output_df.to_csv('validation_data/word_error_rates.csv', index=False)















 