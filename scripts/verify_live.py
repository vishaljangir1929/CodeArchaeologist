"""Exercise actual local models against the reference project and save inspectable results."""
from __future__ import annotations
import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:8765')
    parser.add_argument('--output',default='verification/live-model-results.json')
    args=parser.parse_args()
    base=args.url.rstrip('/')+'/api'
    def request(path,body=None):
        data=json.dumps(body).encode() if body is not None else None
        req=urllib.request.Request(base+path,data=data,headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=240) as response:
            return json.load(response)
    status=request('/ai/status')
    if not status['generation']['ready'] or not status['embeddings']['ready']:
        raise RuntimeError('Both real local models must be ready for this verification.')
    project=next(item for item in request('/projects') if item['source_kind']=='demo' and item['status']=='ready')
    prefix='/projects/'+project['id']
    analysis=request(prefix+'/analysis')
    cases=[
        ('How are product prices and quantities added together?', 'calculate_total'),
        ('Where is a purchase confirmation email sent?', 'send_receipt'),
        ('How is a discount determined for loyal customers?', 'loyalty_discount'),
        ('Where are empty carts and invalid quantities checked?', 'CheckoutService.validate_cart'),
    ]
    evaluations=[]
    for question,expected in cases:
        result=request(prefix+'/search?'+urllib.parse.urlencode({'q':question,'limit':6}))
        names=[item['name'] for item in result['results']]
        symbol=next(item for item in analysis['functions'] if item['qualified_name']==expected)
        source_hit=any(item['file']==symbol['file'] and item['line_start']<=symbol['line_start']
                       and item['line_end']>=symbol['line_end'] for item in result['results'][:3])
        evaluations.append({'question':question,'expected_symbol':expected,'retrieval_mode':result['mode'],
                            'top_symbols':names,'hit_at_3':expected in names[:3],'hit_at_6':expected in names,
                            'source_evidence_hit_at_3':source_hit})
        print('Retrieval:',question,'=>',names[:3],flush=True)
    start=time.perf_counter()
    answer=request(prefix+'/ask',{'question':'How does calculate_total compute the amount from cart items? Explain only the code and cite the source.'})
    elapsed=round(time.perf_counter()-start,2)
    print('Real AI response:',answer['answer'],flush=True)
    report=request(prefix+'/analysis')
    function=next(item for item in report['functions'] if item['qualified_name']=='calculate_total')
    explanation=request(prefix+'/explain',{'symbol_id':function['id']})
    print('Real symbol explanation:',explanation['answer'],flush=True)
    receipt=request(prefix+'/ask',{'question':'What does send_receipt return? Does the provided source actually send an email? Distinguish its return value from real network I/O.'})
    print('Receipt behavior check:',receipt['answer'],flush=True)
    result={'status':status,'sample_project':project['name'],'retrieval_cases':evaluations,
            'hit_at_3':sum(item['hit_at_3'] for item in evaluations),
            'source_evidence_hit_at_3':sum(item['source_evidence_hit_at_3'] for item in evaluations),
            'case_count':len(evaluations),'question_answer':answer,'question_seconds':elapsed,
            'symbol_explanation':explanation,
            'receipt_behavior_answer':receipt,
            'scope':'Small reference-project functional check, not a general accuracy benchmark. Answers require human source review.'}
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Saved',output,flush=True)


if __name__=='__main__':
    main()
